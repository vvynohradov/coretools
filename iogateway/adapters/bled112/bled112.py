# This file is copyright Arch Systems, Inc.
# Except as otherwise provided in the relevant LICENSE file, all rights are reserved.

from Queue import Queue
import time
import struct
import threading
import logging
import datetime
import uuid
import copy
import serial
from iotilecore.utilities.packed import unpack
from ..async_packet import AsyncPacketBuffer
from ..adapter import DeviceAdapter
from bled112_cmd import BLED112CommandProcessor
from tilebus import *

def packet_length(header):
    """
    Find the BGAPI packet length given its header
    """

    highbits = header[0] & 0b11
    lowbits = header[1]

    return (highbits << 8) | lowbits

class BLED112Adapter(DeviceAdapter):
    """Callback based BLED112 wrapper supporting multiple simultaneous connections
    """

    ExpirationTime = 60 #Expire devices 60 seconds after seeing them

    def __init__(self, port, on_scan=None, on_disconnect=None, passive=True):
        super(BLED112Adapter, self).__init__()

        if on_scan is not None:
            self.add_callback('on_scan', on_scan)

        if on_disconnect is not None:
            self.add_callback('on_disconnect', on_disconnect)

        self._serial_port = serial.Serial(port, 256000, timeout=0.01, rtscts=True)
        self._stream = AsyncPacketBuffer(self._serial_port, header_length=4, length_function=packet_length)
        self._commands = Queue()
        self._command_task = BLED112CommandProcessor(self._stream, self._commands)
        self._command_task.event_handler = self._handle_event
        self._command_task.start()

        #Prepare internal state of scannable and in progress devices
        self.partial_scan_responses = {}
        self._connections = {}
        self.count_lock = threading.Lock()
        self.connecting_count = 0
        self.maximum_connections = 0

        self._logger = logging.getLogger('ble.manager')
        self._command_task._logger.setLevel(logging.WARNING)

        self.scanning = False
        self._active_scan = not passive

        try:
            self.initialize_system_sync()
            self.start_scan(self._active_scan)
        except:
            self.stop()
            raise

    def can_connect(self):
        """Check if this adapter can take another connection

        Returns:
            bool: whether there is room for one more connection
        """

        return len(self._connections) < self.maximum_connections

    def _handle_event(self, event):        
        if event.command_class == 6 and event.command == 0:
            #Handle scan response events
            self._parse_scan_response(event)
        elif event.command_class == 3 and event.command == 4:
            #Handle disconnect event
            conn, reason = unpack("<BH", event.payload)
            if conn not in self._connections:
                self._logger.warn("Disconnection event for conn not in table %d", conn)
                return

            conndata = self._get_connection(conn)
            state = conndata['state']
            self._logger.warn('Disconnection event, handle=%d, reason=0x%X, state=%s', conn, reason,
                              state)

            if state == 'preparing':
                conndata['failure_reason'] = 'Early disconnect, reason=%s' % reason
            elif state == 'started':
                pass
            elif state == 'connected':
                pass

            if 'disconnect_handler' in conndata:
                callback = conndata['disconnect_handler']
                callback(conndata['connection_id'], conn, True, 'Disconnected')

            if conn in self._connections:
                del self._connections[conn]
        else:
            self._logger.warn('Unhandled BLE event: ' + str(event))

    def _parse_scan_response(self, response):
        """Parse the IOTile specific data structures in the BLE advertisement packets and add the device to our list of scanned devices
        """

        payload = response.payload
        length = len(payload) - 10

        if length < 0:
            return #FIXME: Log an error here

        rssi, packet_type, sender, addr_type, bond, data = unpack("<bB6sBB%ds" % length, payload)

        parsed ={}
        parsed['rssi'] = rssi
        parsed['type'] = packet_type
        parsed['address_raw'] = sender
        parsed['address'] = ':'.join([format(ord(x), "02X") for x in sender[::-1]])
        parsed['address_type'] = addr_type

        #Scan data is prepended with a length
        if len(data)  > 0:
            parsed['scan_data'] = bytearray(data[1:])
        else:
            parsed['scan_data'] = bytearray([])

        #If this is an advertisement response, see if its an IOTile device
        if parsed['type'] == 0 or parsed['type'] == 6:
            scan_data = parsed['scan_data']

            if len(scan_data) < 29:
                return #FIXME: Log an error here

            #Skip BLE flags
            scan_data = scan_data[3:]

            #Make sure the scan data comes back with an incomplete UUID list
            if scan_data[0] != 17 or scan_data[1] != 6:
                return #FIXME: Log an error here
            
            uuid_buf = scan_data[2:18]
            assert len(uuid_buf) == 16
            service = uuid.UUID(bytes_le=str(uuid_buf))

            if service == TileBusService:
                #Now parse out the manufacturer specific data
                manu_data = scan_data[18:]
                assert len(manu_data) == 10

                #FIXME: Move flag parsing code flag definitions somewhere else
                length, datatype, manu_id, device_uuid, flags = unpack("<BBHLH", manu_data)
                
                pending = False
                low_voltage = False
                user_connected = False
                if flags & (1 << 0):
                    pending = True
                if flags & (1 << 1):
                    low_voltage = True
                if flags & (1 << 2):
                    user_connected = True

                info = {'user_connected': user_connected, 'connection_string': parsed['address'], 
                        'uuid': device_uuid, 'pending_data': pending, 'low_voltage': low_voltage, 
                        'signal_strength': parsed['rssi']}

                if not self._active_scan:
                    self._trigger_callback('on_scan', self.id, info, self.ExpirationTime)
                else:
                    self.partial_scan_responses[parsed['address']] = info
        elif parsed['type'] == 4 and parsed['address'] in self.partial_scan_responses:
            #Check if this is a scan response packet from an iotile based device
            scan_data = parsed['scan_data']
            if len(scan_data) != 31:
                return #FIXME: Log an error here

            length, datatype, manu_id, voltage, stream, reading, reading_time, curr_time = unpack("<BBHHHLLL11x", scan_data)
            
            info = self.partial_scan_responses[parsed['address']]
            info['voltage'] = voltage / 256.0
            info['current_time'] = curr_time
            info['last_seen'] = datetime.datetime.now()

            if stream != 0xFFFF:
                info['visible_readings'] = [(stream, reading_time, reading),]

            del self.partial_scan_responses[parsed['address']]
            self._trigger_callback('on_scan', self.id, info, self.ExpirationTime)

    def stop(self):
        """Safely stop this BLED112 instance without leaving it in a weird state

        """

        if self.scanning:
            self.stop_scan()

        #Make a copy since this will change size as we disconnect
        con_copy = copy.copy(self._connections)

        for _, context in con_copy.iteritems():
            self.disconnect_sync(context['connection_id'])

        self._command_task.stop()
        self._stream.stop()

    def stop_scan(self):
        self._command_task.sync_command(['_stop_scan'])
        self.scanning = False

    def start_scan(self, active):
        self._command_task.sync_command(['_start_scan', active])
        self.scanning = True

    def connect(self, connection_string, conn_id, callback):
        """Connect to a device by its connection_string

        This function asynchronously connects to a device by its BLE address passed in the
        connection_string parameter and calls callback when finished.  Callback is called
        on either success or failure with the signature:

        callback(conn_id: int, result: bool, value: None)

        Args:
            connection_string (string): A BLE address is XX:YY:ZZ:AA:BB:CC format
            conn_id (int): A unique integer set by the caller for referring to this connection
                once created
            callback (callable): A callback function called when the connection has succeeded or
                failed
        """

        context = {}
        context['connection_id'] = conn_id
        context['callback'] = callback

        #Don't scan while we attempt to connect to this device
        if self.scanning:
            self.stop_scan()

        with self.count_lock:
            self.connecting_count += 1

        self._command_task.async_command(['_connect', connection_string],
                                         self._on_connection_finished, context)

    def enable_rpcs(self, conn_id, callback):
        """Enable RPC interface for this IOTile device

        Args:
            conn_id (int): the unique identifier for the connection
            callback (callback): Callback to be called when this command finishes
        """

        handle = self._find_handle(conn_id)
        services = self._connections[handle]['services']

        self._command_task.async_command(['_enable_rpcs', handle, services], self._enable_rpcs_finished, {'connection_id': conn_id, 'callback': callback})

    def _enable_rpcs_finished(self, result):
        success, retval, context = self._parse_return(result)
        callback = context['callback']

        callback(success, retval)

    def probe_services(self, handle, conn_id, callback):
        """Given a connected device, probe for its GATT services and characteristics

        Args:
            handle (int): a handle to the connection on the BLED112 dongle
            conn_id (int): a unique identifier for this connection on the DeviceManager
                that owns this adapter.
            callback (callable): Callback to be called when this procedure finishes
        """

        self._command_task.async_command(['_probe_services', handle], callback,
                                         {'connection_id': conn_id, 'handle': handle})

    def probe_characteristics(self, conn_id, handle, services):
        """Probe a device for all characteristics defined in its GATT table

        This routine must be called after probe_services and passed the services dictionary
        produced by that method.

        Args:
            handle (int): a handle to the connection on the BLED112 dongle
            conn_id (int): a unique identifier for this connection on the DeviceManager
                that owns this adapter.
            services (dict): A dictionary of GATT services produced by probe_services()
        """
        self._command_task.async_command(['_probe_characteristics', handle, services],
            self._probe_characteristics_finished, {'connection_id': conn_id, 'handle': handle, 
                                                   'services': services})

    def initialize_system_sync(self):
        """Remove all active connections and query the maximum number of supported connections
        """

        retval = self._command_task.sync_command(['_query_systemstate'])
        
        self.maximum_connections = retval['max_connections']

        for conn in retval['active_connections']:
            self._connections[conn] = {'handle': conn, 'connection_id': len(self._connections)}
            self.disconnect_sync(0)

        self._logger.critical("BLED112 adapter supports %d connections", self.maximum_connections)

    def disconnect(self, conn_id, callback):
        """Disconnect from a device that has previously been connected

        Args:
            conn_id (int): a unique identifier for this connection on the DeviceManager
                that owns this adapter.
            callback (callable): A function called as callback(conn_id, handle, success, reason)
            when the disconnection finishes.  Disconnection can only either succeed or timeout.
        """

        found_handle = None
        #Find the handle by connection id
        for handle, conn in self._connections.iteritems():
            if conn['connection_id'] == conn_id:
                found_handle = handle

        if found_handle is None:
            callback(conn_id, 0, False, 'Invalid connection_id')
            return

        self._command_task.async_command(['_disconnect', found_handle], self._on_disconnect,
                                         {'connection_id': conn_id, 'handle': found_handle,
                                          'callback': callback})

    def disconnect_sync(self, conn_id):
        """Synchronously disconnect from a connected device

        """
        done = threading.Event()

        def disconnect_done(conn_id, handle, status, reason):
            done.set()

        self.disconnect(conn_id, disconnect_done)
        done.wait()

    def _on_disconnect(self, result):
        """Callback called when disconnection command finishes

        Args:
            result (dict): result returned from diconnection command
        """
        
        success, _, context = self._parse_return(result)

        callback = context['callback']
        connection_id = context['connection_id']
        handle = context['handle']

        del self._connections[handle]

        callback(connection_id, handle, success, "No reason given")

    @classmethod
    def _parse_return(cls, result):
        """Extract the result, return value and context from a result object
        """

        return_value = None
        success = result['result']
        context = result['context']

        if 'return_value' in result:
            return_value = result['return_value']

        return success, return_value, context

    def _find_handle(self, conn_id):
        for handle, data in self._connections.iteritems():
            if data['connection_id'] == conn_id:
                return handle

        raise ValueError("connection id not found: %d" % conn_id)

    def _get_connection(self, handle, expect_state=None):
        """Get a connection object, logging an error if its in an unexpected state
        """

        conndata = self._connections[handle]

        if expect_state is not None and conndata['state'] != expect_state:
            self._logger.error("Connection in unexpected state, wanted=%s, got=%s", expect_state,   
                               conndata['state'])
        return conndata

    def _on_connection_finished(self, result):
        """Callback when the connection attempt to a BLE device has finished

        This function if called when a new connection is successfully completed

        Args:
            event (BGAPIPacket): Connection event
        """

        success, retval, context = self._parse_return(result)
        conn_id = context['connection_id']
        callback = context['callback']

        if success is False:
            callback(conn_id, False, 'Timeout openning connection id %d' % conn_id)
            with self.count_lock:
                self.connecting_count -= 1
            return

        handle = retval['handle']
        context['disconnect_handler'] = self._on_connection_failed
        context['connect_time'] = time.time()
        context['state'] = 'preparing'
        self._connections[handle] = context

        self.probe_services(handle, conn_id, self._probe_services_finished)

    def _on_connection_failed(self, conn_id, handle, clean, reason):
        """Callback called from another thread when a connection attempt has failed.
        """

        with self.count_lock:
            self.connecting_count -= 1

        self._logger.info("_on_connection_failed conn_id=%d, reason=%s", conn_id, str(reason))

        conndata = self._get_connection(handle)
        callback = conndata['callback']
        conn_id = conndata['connection_id']
        failure_reason = conndata['failure_reason']
        callback(conn_id, False, failure_reason)

        del self._connections[handle]

    def _probe_services_finished(self, result):
        """Callback called after a BLE device has had its GATT table completely probed

        Args:
            result (dict): Parameters determined by the probe and context passed to the call to
                probe_device()
        """

        #If we were disconnected before this function is called, don't proceed
        handle = result['context']['handle']
        conn_id = result['context']['connection_id']

        if handle not in self._connections:
            self._logger.info('Connection disconnected before prob_services_finished, conn_id=%d',
                              conn_id)
            return


        conndata = self._get_connection(handle, 'preparing')

        if result['result'] is False:
            conndata['failed'] = True
            conndata['failure_reason'] = 'Could not probe GATT services'
            self.disconnect(conn_id, self._on_connection_failed)
        else:
            conndata['services_done_time'] = time.time()
            self.probe_characteristics(result['context']['connection_id'], result['context']['handle'], result['return_value']['services'])

    def _on_disconnect_started(self, result):
        """Callback called when an attempt to disconnect from a device has been initiated
        """

        handle = result['context']['handle']
        callback = result['context']['callback']
        conn_id = result['context']['connection_id']
        conndata = self._get_connection(handle)

        if result['result'] is False:
            self._logger.error('Could not disconnect cleanly from device handle=%d', handle)
            callback(conn_id, handle, False, 'Could not initiate disconnection proces from device')
            conndata['state'] = 'zombie'
            return

        #We have started the disconnection process
        conndata['disconnecting'] = True

    def _probe_characteristics_finished(self, result):
        """Callback when BLE adapter has finished probing services and characteristics for a device 

        Args:
            result (dict): Result from the probe_characteristics command
        """

        handle = result['context']['handle']
        conn_id = result['context']['connection_id']

        if handle not in self._connections:
            self._logger.info('Connection disconnected before probe_char... finished, conn_id=%d',
                              conn_id)
            return

        conndata = self._get_connection(handle, 'preparing')
        callback = conndata['callback']

        if result['result'] is False:
            conndata['failed'] = True
            conndata['failure_reason'] = 'Could not probe GATT characteristics'
            self.disconnect(conn_id, self._on_connection_failed)
            return

        #Validate that this is a proper IOTile device
        services = result['return_value']['services']
        if TileBusService not in services:
            conndata['failed'] = True
            conndata['failure_reason'] = 'TileBus service not present in GATT services'
            self.disconnect(conn_id, self._on_connection_failed)
            return

        conndata['chars_done_time'] = time.time()
        service_time = conndata['services_done_time'] - conndata['connect_time']
        char_time = conndata['chars_done_time'] - conndata['services_done_time']
        total_time = service_time + char_time
        conndata['state'] = 'connected'
        conndata['services'] = services

        del conndata['disconnect_handler']

        with self.count_lock:
            self.connecting_count -= 1

        self._logger.info("Total time to connect to device: %.3f (%.3f enumerating services, %.3f enumerating chars)", total_time, service_time, char_time)
        callback(conndata['connection_id'], True, None)

    def periodic_callback(self):
        """Periodic cleanup tasks to maintain this adapter, should be called every second
        """

        #Check if we should start scanning again
        if not self.scanning and len(self._connections) == 0 and self.connecting_count == 0:
            self._logger.info("Restarting scan for devices")
            self.start_scan(self._active_scan)
            self._logger.info("Finished restarting scan for devices")

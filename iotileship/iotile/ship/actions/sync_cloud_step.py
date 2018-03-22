from __future__ import (unicode_literals, print_function, absolute_import)
from builtins import str
from iotile.cloud.cloud import IOTileCloud
from iotile.core.exceptions import ArgumentError

class SyncCloudStep(object):
    """A Recipe Step used to synchronize the device with the POD

    Checks if the cloud settings are properly set.

    Args:
        uuid (int): Target Device
        device_template (str): Optional. Device template name to change to in cloud
        sensorgraph (str): Optional. Sensorgraph name to change to in cloud
        expected_os_tag (str): Optional. Expected os tag to check against in cloud
        expected_app_tag (str): Optional. Expected app tag to check against in cloud
        unclaim (bool) : Optional. Defaults to false. Unclaim device after checking if True
        edit_settings (bool) : Optional Defaults to false. Change cloud settings if True, 
            raises errors if cloud settings are inconsistent
    """
    def __init__(self, args):
        if args.get('uuid') is None:
            raise ArgumentError("SyncCloudStep Parameter Missing", parameter_name='uuid')
        self._uuid              = args['uuid']

        self._device_template   = args.get('device_template')
        self._expected_os_tag   = args.get('expected_os_tag')

        self._sensorgraph       = args.get('sensorgraph')
        self._expected_app_tag  = args.get('expected_app_tag')

        self._unclaim           = args.get('unclaim', False)
        self._edit_settings     = args.get('edit_settings', False)

    def run(self):
        cloud = IOTileCloud()
        info = cloud.device_info(self._uuid)

        if self._sensorgraph is not None:
            if info['sg'] != self._sensorgraph:
                if self._edit_settings:
                    print("--> Updating cloud sensorgraph from %s to %s" % \
                        (info['sg'], self._sensorgraph))
                    cloud.set_sensorgraph(self._uuid, self._sensorgraph, app_tag=self._expected_app_tag)
                else:
                    raise ArgumentError('Cloud has incorrect sensorgraph, need to edit', 
                            current_setting=info['sg'], )

        if self._device_template is not None:
            if info['template'] != self._device_template:
                if self._edit_settings:
                    print("--> Updating cloud device template from %s to %s" % \
                        (info['template'], self._device_template))
                    cloud.set_device_template(self._uuid, self._device_template, os_tag=self._expected_os_tag)
                else:
                    raise ArgumentError('Cloud has incorrect sensorgraph, need to edit', )

        if self._unclaim:
            print("--> Unclaiming device")
            cloud.unclaim(self._uuid)

"""Classes handling the various authentication key types used in device security.

All Authentication keys currently are 256-bits long.

There are three major classes of Authentication keys:

- Root Keys: Are sources of identity for a device.  They are used only to
    produce other keys that are then used to sign or encrypt data.
- Report Signing Keys: Are one-time-use keys created to sign a report from
    an IOTile device in order to guarantee its origin.
- User Tokens: Are tokens given to users to allow them to login to an IOTile
    device and control it in the field.
- Session Keys: Are short lived authentication keys used to protect a session
    between a user and a device.
"""

import hashlib
import hmac
import struct
from iotile.core.exceptions import ArgumentError, DataError


class DevicePermissions(object):
    """A list of permissions for what can be done to an IOTile Device.

    Device permissions are high level access rights that a user is
    granted on the basis of a specific scoped token that they provide
    when they connect to the device.

    Possible permissions are:
    - receive_streams: Allow the user to receive streaming data from a
        device.
    - whitelisted_rpcs: Allow the user to send whitelisted RPCs to the
        device.
    - all_rpcs: Allow the user to send all RPCs to the device.
    - send_scripts: Allow the user to send scripts to the device.
    - receive_traces: Allow the user to receive tracing data from the
        device.

    Args:
        **kwargs: A list of the named permissions that you want to
            add to this DevicePermissions object.
    """

    def __init__(self, **kwargs):
        self.receive_streams = kwargs.get('receive_streams', False)
        self.whitelisted_rpcs = kwargs.get('whitelisted_rpcs', False)
        self.all_rpcs = kwargs.get('all_rpcs', False)
        self.send_scripts = kwargs.get('send_scripts', False)
        self.receive_traces = kwargs.get('receive_traces', False)

    def encode(self):
        """return an encoded integer containing these permissions."""

        receive_streams = int(self.receive_streams)
        whitelisted_rpcs = int(self.whitelisted_rpcs)
        all_rpcs = int(self.all_rpcs)
        send_scripts = int(self.send_scripts)
        receive_traces = int(self.receive_traces)

        return (receive_streams << 0) | (send_scripts << 1) | (whitelisted_rpcs << 2) | (all_rpcs << 3) | (receive_traces << 4)

    @classmethod
    def Decode(cls, encoded_perms):
        """Decode permissions created by DevicePermissions.encode().

        Args:
            encoded_perms (int): The encoded permissions to decode

        Returns:
            DevicePermissions: The decoded permissions
        """

        if encoded_perms < 0 or encoded_perms >= (1 << 5):
            raise ArgumentError("Encoded permissions integer contains permissions that DevicePermisions does not understand", encoded_perms=encoded_perms)

        receive_streams = bool(encoded_perms & (1 << 0))
        send_scripts = bool(encoded_perms & (1 << 1))
        whitelisted_rpcs = bool(encoded_perms & (1 << 2))
        all_rpcs = bool(encoded_perms & (1 << 3))
        receive_traces = bool(encoded_perms & (1 << 4))

        return DevicePermissions(receive_streams=receive_streams, send_scripts=send_scripts, whitelisted_rpcs=whitelisted_rpcs, all_rpcs=all_rpcs, receive_traces=receive_traces)


class AuthKey(object):
    """An authentication key that can be used to sign or encrypt data.

    There are various kinds of authentication keys for each IOTile device and
    some authentication keys can be used to generate other kinds of keys.

    Args:
        device_id (int): The device ID for which this key applies.
        key_type (int): The type of key that this is, as defined in an AuthKey
            constant.
        key (bytes): An optional value for the key material itself.  Sometimes
            AuthKey instances are created without directly specifying the key
            material and used to communicate what type of key is desired.
        root_key (int): If this key itself is not a root key specifies what
            the root key for generating the key was (either a UserKey or a DeviceKey)
        **kwargs: Optional metadata associated with this key.

    """

    # All keys are 256 bits
    KeyLength = 32

    # Known Key Types
    RootUserKey = 0
    RootDeviceKey = 1
    ReportSigningKey = 2
    UserToken = 3
    ScopedUserToken = 4
    SessionKey = 5

    KnownTypes = frozenset([RootUserKey, RootDeviceKey, ReportSigningKey, UserToken, ScopedUserToken, SessionKey])

    def __init__(self, device_id, key_type, key=None, root_key=None, **kwargs):
        if key_type not in AuthKey.KnownTypes:
            raise ArgumentError("Unknown key type specified for AuthKey", key_type=key_type)

        if key_type not in [AuthKey.RootUserKey, AuthKey.RootDeviceKey] and root_key is None:
            raise ArgumentError("You must specify a root source key type for a not root AuthKey", key_type=key_type)
        elif key_type in [AuthKey.RootUserKey, AuthKey.RootDeviceKey]:
            root_key = key_type

        self.key_type = key_type
        self.root_key = root_key
        self.device_id = device_id

        self.key = self.set_key(key)
        self.metadata = kwargs

    def set_key(self, key):
        """Set or change the actual key associated with this AuthKey.

        Args:
            key (bytes): An optional value for the key material itself.  Sometimes
                AuthKey instances are created without directly specifying the key
                material and used to communicate what type of key is desired.
        """

        if key is not None:
            if not isinstance(key, [bytes, bytearray]):
                raise ArgumentError("Key material is not of the correct type, should be bytes or bytearray", type=key.__class__.__name__)

            if isinstance(key, bytearray):
                key = bytes(key)

            if len(key) != AuthKey.KeyLength:
                raise ArgumentError("Key material was not of the correct length", required_length=AuthKey.KeyLength, length=len(key))

        self.key = key

    def create_report_signing_key(self, report_id, report_timestamp):
        """Create a report signing key.

        The type of this auth key must be either RootUserKey or RootDeviceKey
        in order to generate a report signing key.  Report signing keys are
        one-time-use keys generated using HMAC-SHA256 as follows:

        signing_key = HMAC(root key, report_id || report_timestamp)

        Args:
            report_id (int): The id of the report that you would like to create
                a signing key for.
            report_timestamp (int): The sent_timestamp of the report as reported
                by the IOTile device.

        Returns:
            AuthKey: a ReportSigningKey type AuthKey with the key material correctly derived.
        """

        if self.key is None:
            raise DataError("No key material was specified but an operation requiring key material was attempted")

        if self.key_type not in [AuthKey.RootUserKey, AuthKey.RootDeviceKey]:
            raise DataError("You can only create a report signing key from a Root Key", key_type=self.key_type)

        signed_message = struct.pack("<LLL", 0x00000002, report_id, report_timestamp)
        report_keydata = hmac.new(self.key, signed_message, hashlib.sha256).digest()

        return AuthKey(self.device_id, AuthKey.ReportSigningKey, key=report_keydata, root_key=self.root_key, report_id=report_id, report_timestamp=report_timestamp)

    def create_user_token(self, generation):
        """Create a user token from a root authentication key.

        A User Token is a key that is associated with a 16 bit generation number.
        The generation number allows revoking previously granted user tokens by
        telling a device to require a certain generation of user token to allow
        access.

        Args:
            generation (int): A number between 0 and 65535 inclusive.

        Returns:
            AuthKey: a UserToken type AuthKey with the key material correctly derived.
        """
        if self.key is None:
            raise DataError("No key material was specified but an operation requiring key material was attempted")

        if self.key_type not in [AuthKey.RootUserKey, AuthKey.RootDeviceKey]:
            raise DataError("You can only create a user token from a Root Key", key_type=self.key_type)

        if generation < 0 or generation >= (1 << 16):
            raise ArgumentError("Invalid generation specified for UserToken, must be in [0, 65535]", generation=generation)

        signed_message = struct.pack("<LL", 0x00000001, generation)
        token_data = hmac.new(self.key, signed_message, hashlib.sha256).digest()

        return AuthKey(self.device_id, AuthKey.UserToken, key=token_data, root_key=self.key_type, generation=generation)

    def create_scoped_token(self, permissions, generation=None):
        """Create a scoped user token from either a root key or an (unscoped) user token.

        Args:
            permissions (DevicePermissions): A set of permissions to grant to this scoped token
            generation (int): If this is a root key, the generation of intermediate UserToken to
                create before creating the ScopedToken.

        Returns:
            AuthKey: a ScopedToken type AuthKey with the key material correctly derived.
        """

        if self.key is None:
            raise DataError("No key material was specified but an operation requiring key material was attempted")

        parent_key = None
        if self.key_type in [AuthKey.RootUserKey, AuthKey.RootDeviceKey]:
            if generation is None:
                raise ArgumentError("You must specify a generation to create a ScopedToken from a RootKey")

            parent_key = self.create_user_token(generation)
        elif self.key_type == AuthKey.UserToken:
            parent_key = self
        else:
            raise DataError("Attempting to create a ScopedToken from an invalid parent key", key_type=self.key_type)

        signed_message = struct.pack("<L", permissions.encode())
        token_data = hmac.new(parent_key.key, signed_message, hashlib.sha256).digest()

        return AuthKey(self.device_id, AuthKey.ScopedUserToken, key=token_data, root_key=parent_key.root_key, generation=parent_key.metadata['generation'], permissions=permissions)

    def create_session_key(self, client_nonce, server_nonce, permissions=None, generation=None):
        """Create a session key.

        The key used to create the session key can either be a Root Key, a UserToken or a ScopedUserToken.
        If a Root Key or a UserToken is used, permissions and possibly a generation number are required to create
        the appropriate intermediate keys.

        Args:
            client_nonce (bytes): 16 bytes of nonce data provided by the client of the session
            server_nonce (bytes): 16 bytes of nonce data provided by the server of the session
            permissions (DevicePermissions): A set of permissions to grant to this scoped token
            generation (int): If this is a root key, the generation of intermediate UserToken to
                create before creating the ScopedToken.

        Returns:
            AuthKey: A SessionKey type AuthKey with the key material correctly derived
        """

        if self.key is None:
            raise DataError("No key material was specified but an operation requiring key material was attempted")

        parent_key = self

        if self.key_type in [AuthKey.RootUserKey, AuthKey.RootDeviceKey]:
            if permissions is None or generation is None:
                raise ArgumentError("You must pass a DevicePermissions and generation when creating a session key directly from a root key")

            parent_key = self.create_scoped_token(permissions, generation)
        elif self.key_type == AuthKey.UserToken:
            if permissions is None:
                raise ArgumentError("You must pass a DevicePermissions when creating a session key directly from a UserToken")

            parent_key = self.create_scoped_token(permissions)

        if parent_key.key_type != AuthKey.ScopedUserToken:
            raise ArgumentError("You must provide a ScopedUserToken, a RootKey or a UserToken to create a session key.")

        if len(client_nonce) != 16 or len(server_nonce) != 16:
            raise ArgumentError("You must provide 128 bits of client nonce and 128 bits of server nonce to create a session key", client_length=len(client_nonce), server_length=len(server_nonce))

        signed_message = bytes(client_nonce) + bytes(server_nonce)
        token_data = hmac.new(parent_key.key, signed_message, hashlib.sha256).digest()

        return AuthKey(parent_key.device_id, AuthKey.SessionKey, key=token_data, root_key=parent_key.root_key,
                       generation=parent_key.metadata['generation'], permissions=parent_key.metadata['permissions'])

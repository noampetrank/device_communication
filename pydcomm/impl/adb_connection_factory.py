from pydcomm.general_android.connection.internal_connection_factory import InternalAdbConnectionFactory
from pydcomm.general_android.connection.device_selector import adb_devices, get_device_to_connect_user_choice
from pydcomm.impl.adb_connection_adapter import AdbConnection

from pydcomm.public.iconnection import ConnectionFactory


class WiredAdbConnectionFactory(ConnectionFactory):
    @classmethod
    def create_connection(cls, device_id=None, **kwargs):
        """Create connection

        :param str|None device_id: Specific device id to connect to. If none given, must call `choose_device_id()`.
        :param kwargs:
        :rtype: IConnection
        """
        if not device_id:
            device_id = cls.choose_device_id()
        use_manual_fixes = kwargs.get("use_manual_fixes", True)
        connection = AdbConnection(cls._get_oppo_device(device_id=device_id,
                                                        use_manual_fixes=use_manual_fixes))
        if connection.shell("echo hi") == "hi":
            return connection

    @classmethod
    def connected_devices(cls):
        """Returns list of serial numbers of connected devices.

        :rtype: list[str]
        """
        return map(lambda x: x[1] + " - " + x[2], adb_devices())

    @classmethod
    def choose_device_id(cls):
        """
        This opens a user interface for choosing possible device for this factory.
        :return: String representing device id, that can be passed to `wired_connection` and to `wireless_conenction`.
        :type: str
        """
        return get_device_to_connect_user_choice(filter_wireless_devices=True)

    @classmethod
    def _get_oppo_device(cls, *args, **kwargs):
        connection_factory = InternalAdbConnectionFactory()
        return  connection_factory.get_oppo_wired_device(*args, **kwargs)


class WirelessAdbConnectionFactory(WiredAdbConnectionFactory):
    @classmethod
    def _get_oppo_device(cls, *args, **kwargs):
        connection_factory = InternalAdbConnectionFactory()
        return connection_factory.get_oppo_wireless_device(*args, **kwargs)

    @classmethod
    def choose_device_id(cls):
        """
        This opens a user interface for choosing possible device for this factory.
        :return: String representing device id, that can be passed to `wired_connection` and to `wireless_conenction`.
        :type: str
        """
        return get_device_to_connect_user_choice(filter_wireless_devices=False)

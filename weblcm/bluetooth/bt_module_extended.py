#
# bt_module_extended.py
#
# Bluetooth API for Sentrius IG devices and weblcm
#

import logging
from typing import Optional

import dbus
import dbus.exceptions

from ..utils import DBusManager

from .bt_module import (
    BtMgr,
    DBUS_OBJ_MGR_IFACE,
    BT_OBJ,
    BT_ADAPTER_IFACE,
    BT_OBJ_PATH,
    DBUS_PROP_IFACE,
)


class BtMgrEx(BtMgr):
    """
    Class that manages all bluetooth API functionality
    """

    def __init__(
        self,
        discovery_callback,
        characteristic_property_change_callback,
        connection_callback=None,
        write_notification_callback=None,
        logger: Optional[logging.Logger] = None,
        throw_exceptions=False,
        **kwargs
    ):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        self.logger.info("Initalizing BtMgrEx")
        self.throw_exceptions = throw_exceptions

        self.devices = {}

        # Get DBus objects
        self.manager = dbus.Interface(
            DBusManager().get_system_bus().get_object(BT_OBJ, "/"), DBUS_OBJ_MGR_IFACE
        )
        self.adapter = dbus.Interface(
            DBusManager().get_system_bus().get_object(BT_OBJ, BT_OBJ_PATH),
            BT_ADAPTER_IFACE,
        )
        self.adapter_props = dbus.Interface(
            DBusManager().get_system_bus().get_object(BT_OBJ, BT_OBJ_PATH),
            DBUS_PROP_IFACE,
        )
        self.objects = self.manager.GetManagedObjects()

        # Register signal handlers
        self.manager.connect_to_signal("InterfacesAdded", discovery_callback)
        super(BtMgr, self).__init__(**kwargs)

        # Save custom callbacks with the client
        self.characteristic_property_change_callback = (
            characteristic_property_change_callback
        )
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback

        # Power on the bluetooth module
        self.adapter_props.Set(BT_ADAPTER_IFACE, "Powered", dbus.Boolean(1))


def bt_init_ex(
    discovery_callback,
    characteristic_property_change_callback,
    connection_callback=None,
    write_notification_callback=None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> Optional[BtMgrEx]:
    """
    Initialize the IG bluetooth API
    Returns the device manager instance, to be used in bt_* calls
    """
    try:
        bt = BtMgrEx(
            discovery_callback,
            characteristic_property_change_callback,
            connection_callback,
            write_notification_callback,
            logger,
            **kwargs
        )
        return bt
    except dbus.exceptions.DBusException as e:
        if logger:
            logger.error("Cannot open BT interface: {}".format(e))
        else:
            logging.getLogger(__name__).error("Cannot open BT interface: {}".format(e))
        return None

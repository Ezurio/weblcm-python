#
# bt_module_extended.py
#
# Bluetooth API for Laird Sentrius IG devices and weblcm
#

import logging
from typing import Optional

import dbus
import dbus.exceptions
import dbus.mainloop.glib

from .bt_module import (
    BtMgr,
    DBUS_OBJ_MGR_IFACE,
    BT_OBJ,
    BT_ADAPTER_IFACE,
    BT_OBJ_PATH,
    DBUS_PROP_IFACE,
)

from gi.repository import GLib as glib


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
        setup_dbus_loop=True,
        **kwargs
    ):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        self.logger.info("Initalizing BtMgr")

        self.devices = {}

        # Set up DBus loop
        self.loop = None
        if setup_dbus_loop:
            dbus.mainloop.glib.threads_init()
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.loop = glib.MainLoop()

        # Get DBus objects
        self.manager = dbus.Interface(
            dbus.SystemBus().get_object(BT_OBJ, "/"), DBUS_OBJ_MGR_IFACE
        )
        self.adapter = dbus.Interface(
            dbus.SystemBus().get_object(BT_OBJ, BT_OBJ_PATH), BT_ADAPTER_IFACE
        )
        self.adapter_props = dbus.Interface(
            dbus.SystemBus().get_object(BT_OBJ, BT_OBJ_PATH), DBUS_PROP_IFACE
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

        # Run main loop
        if setup_dbus_loop:
            self.start()


def bt_init_ex(
    discovery_callback,
    characteristic_property_change_callback,
    connection_callback=None,
    write_notification_callback=None,
    logger: Optional[logging.Logger] = None,
    setup_dbus_loop=True,
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
            setup_dbus_loop,
            **kwargs
        )
        return bt
    except dbus.exceptions.DBusException as e:
        if logger:
            logger.error("Cannot open BT interface: {}".format(e))
        else:
            logging.getLogger(__name__).error("Cannot open BT interface: {}".format(e))
        return None

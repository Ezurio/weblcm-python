import cherrypy
import os
import dbus
from syslog import syslog
from xml.etree import ElementTree
from ..systemd_unit import SystemdUnit
from ..definition import (
    WEBLCM_ERRORS,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
    MODEM_FIRMWARE_UPDATE_FILE,
    MODEM_FIRMWARE_UPDATE_DST_DIR,
    MODEM_FIRMWARE_UPDATE_SRC_DIR,
    MODEM_ENABLE_FILE,
    MODEM_CONTROL_SERVICE_FILE,
)
from pathlib import Path
from ..utils import DBusManager


def dbus_to_python(data):
    # convert dbus data types to python native data types
    if isinstance(data, dbus.String):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.UInt32):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.Array):
        data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_key = dbus_to_python(key)
            new_data[str(new_key)] = dbus_to_python(data[key])
        data = new_data
    return data


class Modem(object):

    _bus = DBusManager().get_system_bus()

    def get_modem_location_interface(self, bus):
        _mm_location = "org.freedesktop.ModemManager1.Modem.Location"
        return self.get_modem_interface(bus, _mm_location)

    def get_modem_interface(self, bus, path):

        mm_service = "org.freedesktop.ModemManager1"
        mm_path = "/org/freedesktop/ModemManager1/Modem"

        obj = bus.get_object(mm_service, mm_path)
        if obj:
            iface = dbus.Interface(obj, "org.freedesktop.DBus.Introspectable")
            xml_string = iface.Introspect()
            for child in ElementTree.fromstring(xml_string):
                if child.tag == "node":
                    dev_path = "/".join((mm_path, child.attrib["name"]))
                    dev_obj = bus.get_object(mm_service, dev_path)
                    iface = dbus.Interface(dev_obj, path)
                    return iface
        return None


@cherrypy.expose
class PositioningSwitch(Modem):

    _source = 0

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            "SDCERR": WEBLCM_ERRORS.get("SDCERR_SUCCESS"),
            "positioning": PositioningSwitch._source,
        }
        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {"SDCERR": WEBLCM_ERRORS.get("SDCERR_FAIL")}

        try:
            post_data = cherrypy.request.json
            source = post_data.get("positioning", 0)
            if (PositioningSwitch._source != source) and (
                not source or not PositioningSwitch._source
            ):
                iface = self.get_modem_location_interface(Modem._bus)
                if iface:
                    iface.Setup(dbus.UInt32(source), False)
                    PositioningSwitch._source = source
                    result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_SUCCESS")
        except dbus.exceptions.DBusException as e:
            syslog("Enable/disable positioning: DBUS failed %s" % e)
        except Exception as e:
            syslog("Enable/disable positioning failed: %s" % e)

        result["positioning"] = PositioningSwitch._source
        return result


@cherrypy.expose
class Positioning(Modem):
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {"SDCERR": WEBLCM_ERRORS.get("SDCERR_FAIL")}

        try:
            iface = self.get_modem_location_interface(Modem._bus)
            if iface:
                data = iface.GetLocation()
                result["positioning"] = dbus_to_python(data)
                result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_SUCCESS")
        except dbus.exceptions.DBusException as e:
            syslog("Get positioning data: DBUS failed %s" % e)
        except Exception as e:
            syslog("Get positioning data failed: %s" % e)

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {"SDCERR": WEBLCM_ERRORS.get("SDCERR_FAIL")}

        post_data = cherrypy.request.json
        token = post_data.get("token", 0)
        if not token:
            return result

        try:
            iface = self.get_modem_location_interface(Modem._bus)
            if iface:
                iface.InjectAssistanceData(bytearray(token.encode("utf-8")))
                result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_SUCCESS")
        except dbus.exceptions.DBusException as e:
            syslog("Set token: DBUS failed %s" % e)
        except Exception as e:
            syslog("Set token failed: %s" % e)

        return result


@cherrypy.expose
class ModemFirmwareUpdate(object):
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS.get("SDCERR_FAIL"),
            "InfoMsg": "",
            "Status": "not-updating",  # options are not-updating, in-progress, queued
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] = "Modem firmware update already in progress"
            result["Status"] = "in-progress"
            return result

        if os.path.exists(MODEM_FIRMWARE_UPDATE_FILE):
            result["InfoMsg"] = "Modem firmware update already queued for next boot"
            result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_SUCCESS")
            result["Status"] = "queued"
            return result

        if not os.path.isdir(MODEM_FIRMWARE_UPDATE_SRC_DIR):
            result["InfoMsg"] = "No modem firmware update file available"
            return result

        flist = []
        for path in os.listdir(MODEM_FIRMWARE_UPDATE_SRC_DIR):
            if os.path.isfile(os.path.join(MODEM_FIRMWARE_UPDATE_SRC_DIR, path)):
                flist.append(path)

        if len(flist) == 0:
            result["InfoMsg"] = (
                "No firmware files found in %s" % MODEM_FIRMWARE_UPDATE_SRC_DIR
            )
            return result

        try:
            os.makedirs(MODEM_FIRMWARE_UPDATE_DST_DIR, mode=0o755, exist_ok=True)
        except Exception as e:
            syslog("Unable to create directory: %s" % e)
            result["InfoMsg"] = (
                "Unable to create directory for firmware update file: %s" % e
            )
            return result

        if (len(flist)) > 1:
            result["InfoMsg"] = (
                "Multiple firmware files located in %s - "
                % MODEM_FIRMWARE_UPDATE_SRC_DIR
            )

        try:
            os.symlink(
                os.path.join(MODEM_FIRMWARE_UPDATE_SRC_DIR, flist[0]),
                MODEM_FIRMWARE_UPDATE_FILE,
            )
        except Exception as e:
            syslog("Unable to create symlink: %s" % e)
            result["InfoMsg"] = (
                "Unable to create symlink for firmware update file: %s" % e
            )
            return result

        syslog(
            "Modem firmware update file queued for installation.  File: %s"
            % os.path.join(MODEM_FIRMWARE_UPDATE_SRC_DIR, flist[0])
        )
        result["InfoMsg"] += "Modem Firmware Update queued for next boot"
        result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_SUCCESS")
        result["Status"] = "queued"

        return result

    @cherrypy.tools.json_out()
    def GET(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "No modem firmware update in progress",
            "Status": "not-updating",  # options are not-updating, in-progress, queued
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] = "Modem firmware update in progress"
            result["Status"] = "in-progress"
        elif os.path.exists(MODEM_FIRMWARE_UPDATE_FILE):
            result["InfoMsg"] = "Modem firmware update queued for next boot"
            result["Status"] = "queued"

        return result


@cherrypy.expose
class ModemEnable(SystemdUnit):
    def __init__(self) -> None:
        super().__init__(MODEM_CONTROL_SERVICE_FILE)

    @cherrypy.tools.json_out()
    def GET(self):
        result = {"SDCERR": WEBLCM_ERRORS.get("SDCERR_SUCCESS")}

        enable = False
        if os.path.exists(MODEM_ENABLE_FILE):
            enable = True

        result["modem_enabled"] = True if enable else False
        result["InfoMsg"] = "Modem is %s" % ("enabled" if enable else "disabled")
        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {}
        enable_test = -1
        result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_FAIL")
        try:
            enable = kwargs.get("enable")
            enable = enable.lower()
            if enable in ("y", "yes", "t", "true", "on", "1"):
                enable_test = 1
            elif enable in ("n", "no", "f", "false", "off", "0"):
                enable_test = 0
            if enable_test < 0:
                raise ValueError("illegal value passed in")
        except Exception:
            result["infoMsg"] = (
                "unable to set modem enable. Supplied enable parameter '%s' invalid."
                % kwargs.get("enable")
            )

            return result

        enable = False
        if os.path.exists(MODEM_ENABLE_FILE):
            enable = True

        result["SDCERR"] = WEBLCM_ERRORS.get("SDCERR_SUCCESS")
        if enable and enable_test == 1:
            result["InfoMsg"] = "modem already enabled. No change"
            result["modem_enabled"] = True
        elif (not enable) and enable_test == 0:
            result["InfoMsg"] = "modem already disabled. No change"
            result["modem_enabled"] = False
        else:

            try:
                if enable_test == 1:
                    # enable on device
                    Path(MODEM_ENABLE_FILE).touch()

                    if not self.activate():
                        result["InfoMsg"] = "Unable to enable modem"
                        return
                else:
                    if not self.deactivate():
                        result["InfoMsg"] = "Unable to disable modem"
                        return
                    # disable on device
                    os.remove(MODEM_ENABLE_FILE)
            except Exception as e:
                result["InfoMsg"] = "{}".format(e)
                return result

            result["modem_enabled"] = enable_test == 1
            result["InfoMsg"] = "Modem is %s" % (
                "enabled" if enable_test == 1 else "disabled"
            )
        return result

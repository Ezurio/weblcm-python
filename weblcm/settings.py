import os
import configparser
from . import definition
from threading import Lock

"""
	Weblcm-python system settings manage based on configParser
"""


class WeblcmConfigManage(object):

    """
    Weblcm-setting.ini has multi sections:
    1. Each user has a section with username as the section name;
    2. Other system settings should be saved in 'settings' section;
    """

    _lock = Lock()
    _parser = configparser.ConfigParser(defaults=None)
    _filename = definition.WEBLCM_PYTHON_SETTINGS_FILE
    if os.path.isfile(_filename):
        _parser.read(_filename)

    @classmethod
    def verify_section(cls, section):
        with cls._lock:
            if cls._parser.has_section(section):
                return True
        return False

    @classmethod
    def add_section(cls, section):
        with cls._lock:
            if not cls._parser.has_section(section):
                cls._parser.add_section(section)
                return True
        return False

    @classmethod
    def remove_section(cls, section):
        with cls._lock:
            if cls._parser.has_section(section):
                cls._parser.remove_section(section)
                return True
        return False

    @classmethod
    def update_key_from_section(cls, section, key, val):
        with cls._lock:
            if cls._parser.has_section(section):
                cls._parser.set(section, key, val)
                return True
        return False

    @classmethod
    def get_key_from_section(cls, section, key, fallback=None):
        if cls._parser.has_section(section):
            return cls._parser.get(section, key, fallback=fallback)
        return fallback

    @classmethod
    def delete_key_from_section(cls, section, key):
        with cls._lock:
            if cls._parser.has_section(section):
                cls._parser.remove_option(section, key)

    @classmethod
    def get_section_size_by_key(cls, key):
        cnt = 0
        with cls._lock:
            for k in cls._parser.sections():
                if cls._parser.get(k, key, fallback=None):
                    cnt += 1
        return cnt

    @classmethod
    def get_sections_by_key(cls, key):
        result = []
        with cls._lock:
            for k in cls._parser.sections():
                if cls._parser.get(k, key, fallback=None):
                    result.append(k)
        return result

    @classmethod
    def get_sections_and_key(cls, key):
        result = {}
        with cls._lock:
            for k in cls._parser.sections():
                if cls._parser.get(k, key, fallback=None):
                    result[k] = cls._parser.get(k, key)
        return result

    @classmethod
    def save(cls):
        with cls._lock:
            with open(cls._filename, "w") as fp:
                cls._parser.write(fp)
                return True
        return False


class SystemSettingsManage(object):

    """Manage 'settings' section"""

    section = "settings"

    @classmethod
    def update(cls, key, val):
        return WeblcmConfigManage.update_key_from_section(cls.section, key, val)

    @classmethod
    def get(cls, key, fallback=None):
        return WeblcmConfigManage.get_key_from_section(cls.section, key, fallback)

    @classmethod
    def getInt(cls, key, fallback=None):
        return int(WeblcmConfigManage.get_key_from_section(cls.section, key, fallback))

    @classmethod
    def getBool(cls, key, fallback=None):
        return bool(WeblcmConfigManage.get_key_from_section(cls.section, key, fallback))

    @classmethod
    def update_persistent(cls, key, val):
        WeblcmConfigManage.update_key_from_section(cls.section, key, val)
        return WeblcmConfigManage.save()

    @classmethod
    def delete(cls, key):
        return WeblcmConfigManage.delete_key_from_section(cls.section, key)

    @classmethod
    def delete_persistent(cls, key):
        WeblcmConfigManage.delete_key_from_section(cls.section, key)
        return WeblcmConfigManage.save()

    @classmethod
    def save(cls):
        return WeblcmConfigManage.save()

    @classmethod
    def get_session_timeout(cls):
        "Unit: Minute"
        return int(
            WeblcmConfigManage.get_key_from_section(cls.section, "session_timeout", 10)
        )

    @classmethod
    def get_tamper_protection_timeout(cls):
        "Unit: Second"
        return int(
            WeblcmConfigManage.get_key_from_section(
                cls.section, "tamper_protection_timeout", 600
            )
        )

    @classmethod
    def get_max_web_clients(cls):
        return int(
            WeblcmConfigManage.get_key_from_section(cls.section, "max_web_clients", 1)
        )

    @classmethod
    def get_user_callback_timeout(cls):
        "Unit: Second"
        return int(
            WeblcmConfigManage.get_key_from_section(
                cls.section, "user_callback_timeout", 10
            )
        )

    @classmethod
    def get_login_retry_times(cls):
        return int(
            WeblcmConfigManage.get_key_from_section(cls.section, "login_retry_times", 5)
        )

    @classmethod
    def get_login_retry_window(cls):
        return int(
            WeblcmConfigManage.get_key_from_section(
                cls.section, "login_retry_window", 600
            )
        )

    @classmethod
    def get_log_data_streaming_size(cls):
        return int(
            WeblcmConfigManage.get_key_from_section(
                cls.section, "log_data_streaming_size", 100
            )
        )

    @classmethod
    def get_cert_for_file_encryption(cls):
        return WeblcmConfigManage.get_key_from_section(
            cls.section, "cert_for_file_encryption", "/etc/weblcm-python/ssl/server.crt"
        )

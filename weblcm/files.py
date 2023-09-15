import os
from shutil import copy2, rmtree
from subprocess import run, call
from threading import Lock
from syslog import LOG_ERR, syslog
from typing import Any, List, Tuple
import cherrypy
from .advanced import FactoryReset
from .network_status import NetworkStatusHelper
from . import definition
from .settings import SystemSettingsManage

CONNECTION_TMP_ARCHIVE_FILE = "/tmp/archive.zip"
CONNECTION_TMP_ARCHIVE_DIRECTORY = "/tmp/import"
FILE_READ_SIZE = 8192
UNZIP = "/usr/bin/unzip"
ZIP = "/usr/bin/zip"
NETWORKMANAGER_DIR = "etc/NetworkManager"
PERSISTENT_LOG_PATH = "/var/log/journal/"
VOLATILE_LOG_PATH = "/run/log/journal/"


@cherrypy.expose
class FileManage(object):

    """File Management"""

    _lock = Lock()
    FILE_MANAGE_SCRIPT = "/usr/bin/weblcm-python.scripts/weblcm_files.sh"
    FILE_MANAGE_POST_ZIP_TYPES = ["config", "timezone"]

    # Log will be saved in "/run/log/journal/" for volatile mode  or "/var/log/journal/" for
    # persistent mode. If "/var/log/journal/" exists and "/run/log/journal" is non-empty, the
    # journal should be operating in volatile mode.
    # https://www.freedesktop.org/software/systemd/man/journald.conf.html#Storage=
    _log_data_dir = PERSISTENT_LOG_PATH

    if not os.path.exists(PERSISTENT_LOG_PATH) or (
        os.path.exists(VOLATILE_LOG_PATH) and len(os.listdir(VOLATILE_LOG_PATH)) > 0
    ):
        _log_data_dir = VOLATILE_LOG_PATH

    def save_file(self, type, file):
        path = os.path.normpath(
            os.path.join(definition.FILEDIR_DICT[type], file.filename)
        )
        try:
            with open(path, "wb+") as out:
                while True:
                    data = file.file.read(8192)
                    if not data:
                        break
                    out.write(data)
            return path
        except Exception:
            return None

    def is_encrypted_storage_toolkit_enabled(self) -> bool:
        return os.path.exists(FactoryReset.FACTORY_RESET_SCRIPT)

    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        result = {"SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}

        type = kwargs.get("type", None)
        file = kwargs.get("file", None)

        if not type:
            syslog("FileManage POST - no type specified")
            result["InfoMsg"] = "file POST - no type specified"
            return result

        if not file:
            syslog("FileManage POST - no filename provided")
            result["InfoMsg"] = "file POST - no filename specified"
            return result

        if type not in definition.FILEDIR_DICT:
            syslog(f"FileManage POST type {type} unknown")
            result["InfoMsg"] = f"file POST type {type} unknown"  # bad request
            return result

        if (
            type in FileManage.FILE_MANAGE_POST_ZIP_TYPES
            and not file.filename.endswith(".zip")
        ):
            syslog("FileManage POST type not .zip file")
            result["InfoMsg"] = "file POST type not .zip file"  # bad request
            return result

        try:
            with FileManage._lock:
                fp = self.save_file(type, file)
                if not fp:
                    syslog("FileManage POST type failure to copy file")
                    result["InfoMsg"] = "file POST failure to copy file"  # bad request
                    return result

                if type == "config" and not self.is_encrypted_storage_toolkit_enabled():
                    syslog(
                        "FileManage POST - config import not available on non-encrypted file system images"
                    )
                    raise cherrypy.HTTPError(
                        400,
                        "config import not available on non-encrypted file system images",
                    )

                # Only attempt to unzip the uploaded file if the 'type' requires a zip file. Otherwise,
                # just saving the file is sufficient (i.e., for a certificate)
                if type in FileManage.FILE_MANAGE_POST_ZIP_TYPES:
                    password = kwargs.get("password", "")
                    res = call(
                        [
                            FileManage.FILE_MANAGE_SCRIPT,
                            type,
                            "unzip",
                            fp,
                            definition.FILEDIR_DICT.get(type),
                            password,
                        ]
                    )
                    os.remove(fp)
                    if res:
                        syslog(f"unzip command file '{fp}' failed with error {res}")
                        result[
                            "InfoMsg"
                        ] = f"unzip command failed to unzip provided file.  Error returned: {res}"  # Internal server error
                        return result

                result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
                return result
        except Exception:
            syslog("unable to obtain FileManage._lock")
            result[
                "InfoMsg"
            ] = "unable to obtain internal file lock"  # Internal server error
            return result

    def GET(self, *args, **kwargs):

        type = kwargs.get("type", None)
        if not type:
            syslog("FileManage Get - no filename provided")
            raise cherrypy.HTTPError(400, "no filename provided")

        file = "{0}{1}".format(type, ".zip")
        path = "{0}{1}".format("/tmp/", file)

        if type == "config":

            password = kwargs.get("password", None)
            if not password:
                syslog("FileManage Get - no password provided")
                raise cherrypy.HTTPError(400, "no password provided")

            if not self.is_encrypted_storage_toolkit_enabled():
                syslog(
                    "FileManage GET - config export not available on non-encrypted file system images"
                )
                raise cherrypy.HTTPError(
                    400,
                    "config export not available on non-encrypted file system images",
                )

            args = [
                FileManage.FILE_MANAGE_SCRIPT,
                "config",
                "zip",
                definition.FILEDIR_DICT.get(type),
                path,
                password,
            ]
            syslog("Configuration zipped for user")
        elif type == "log":

            password = kwargs.get("password", None)
            if not password:
                syslog("FileManage Get - no password provided")
                raise cherrypy.HTTPError(400, "no password provided")
            args = [
                FileManage.FILE_MANAGE_SCRIPT,
                "log",
                "zip",
                FileManage._log_data_dir,
                path,
                password,
            ]
            syslog("System log zipped for user")

        elif type == "debug":
            args = [
                FileManage.FILE_MANAGE_SCRIPT,
                "debug",
                "zip",
                " ".join([FileManage._log_data_dir, definition.FILEDIR_DICT["config"]]),
                path,
                SystemSettingsManage.get_cert_for_file_encryption(),
            ]
            syslog("Configuration and system log zipped/encrypted for user")
        else:
            syslog(f"FileManage GET - unknown file type {type}")
            raise cherrypy.HTTPError(400, f"unknown file type {type}")

        try:
            call(args)
        except Exception as e:
            syslog("Script execution error {}".format(e))
            raise cherrypy.HTTPError(400, "Script execution error {}".format(e))

        if os.path.isfile(path):
            objFile = cherrypy.lib.static.serve_file(
                path, "application/x-download", "attachment", file
            )
            os.unlink(path)
            return objFile

        syslog(f"Failed to create file {path} for user")
        raise cherrypy.HTTPError(500, f"failed to create file {path}")

    @cherrypy.tools.json_out()
    def DELETE(self, *args, **kwargs):
        result = {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Unable to delete file",
        }
        type = kwargs.get("type", None)
        file = kwargs.get("file", None)
        if not type or not file:
            if not type:
                syslog("FileManage DELETE - no type specified")
                result["InfoMsg"] = "no type specified"
            if not file:
                syslog("FileManage DELETE - no filename provided")
                result["InfoMsg"] = "no file specified"
            return result
        valid = ["cert", "pac"]
        if type not in valid:
            result["InfoMsg"] = f"type not one of {valid}"
            return result
        path = os.path.normpath(os.path.join(definition.FILEDIR_DICT[type], file))
        if os.path.isfile(path):
            os.remove(path)
            if not os.path.exists(path):
                result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = f"file {file} deleted"
                syslog(f"file {file} deleted")
            else:
                syslog(f"Attempt to remove file {path} did not succeed")
        else:
            syslog(f"Attempt to remove non-existant file {path}")
            result["InfoMsg"] = f"File: {file} not present"
        return result


@cherrypy.expose
class FilesManage(object):
    def import_connections(
        self, import_archive: cherrypy._cpreqbody.Part, password: str
    ) -> Tuple[bool, str]:
        """
        Handle importing NetworkManager connections and certificates from a properly structured and
        encrypted zip archive

        Return value is a tuple in the form of: (success, message)
        """
        if not import_archive:
            return (False, "Invalid archive")

        archive_download_path = os.path.normpath(CONNECTION_TMP_ARCHIVE_FILE)
        result = (False, "Unknown error")
        try:
            # Save the archive to /tmp
            with open(archive_download_path, "wb") as archive_file:
                while True:
                    data = import_archive.file.read(FILE_READ_SIZE)
                    if not data:
                        break
                    archive_file.write(data)

            # Extract the archive using 'unzip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives.
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    UNZIP,
                    "-P",
                    password,
                    "-n",
                    archive_download_path,
                    "-d",
                    CONNECTION_TMP_ARCHIVE_DIRECTORY,
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            # Verify expected sub directories ('system-connections' and 'certs') are present
            if not os.path.exists(
                os.path.join(
                    CONNECTION_TMP_ARCHIVE_DIRECTORY,
                    NETWORKMANAGER_DIR,
                    "system-connections",
                )
            ) or not os.path.exists(
                os.path.join(
                    CONNECTION_TMP_ARCHIVE_DIRECTORY,
                    NETWORKMANAGER_DIR,
                    "certs",
                )
            ):
                raise Exception("Expected files missing")

            # Copy connections and certs
            for subdir in ["system-connections", "certs"]:
                for file in os.listdir(
                    os.path.join(
                        CONNECTION_TMP_ARCHIVE_DIRECTORY,
                        NETWORKMANAGER_DIR,
                        subdir,
                    )
                ):
                    try:
                        source = os.path.join(
                            CONNECTION_TMP_ARCHIVE_DIRECTORY,
                            NETWORKMANAGER_DIR,
                            subdir,
                            file,
                        )
                        dest = os.path.join("/", NETWORKMANAGER_DIR, subdir, file)
                        if os.path.islink(dest):
                            continue
                        copy2(
                            source,
                            dest,
                            follow_symlinks=False,
                        )
                    except Exception:
                        pass

            # Requst NetworkManager to reload connections
            if not NetworkStatusHelper.reload_connections():
                return (False, "Unable to reload connections after import")

            result = (True, "")
        except Exception as e:
            result = (False, str(e))
        finally:
            # Delete the temp file if present
            try:
                os.remove(archive_download_path)
            except OSError:
                pass

            # Delete the temp dir if present
            try:
                rmtree(CONNECTION_TMP_ARCHIVE_DIRECTORY, ignore_errors=True)
            except Exception as e:
                msg = f"Error cleaning up connection imports: {str(e)}"
                return (False, msg)

            return result

    def export_connections(self, password: str) -> Tuple[bool, str, Any]:
        """
        Handle exporting NetworkManager connections and certificates as a properly structured and
        encrypted zip archive

        Return value is a tuple in the form of: (success, message, archive_path)
        """
        archive_download_path = os.path.normpath(CONNECTION_TMP_ARCHIVE_FILE)
        result = (False, "Unknown error", None)
        try:
            # Generate the archive using 'zip' (the built-in Python zipfile implementation is
            # handled in pure Python, is "extremely slow", and does not support generating
            # encrypted archives.
            # https://docs.python.org/3/library/zipfile.html
            proc = run(
                [
                    ZIP,
                    "-P",
                    password,
                    "-9",
                    "-r",
                    archive_download_path,
                    os.path.join("/", NETWORKMANAGER_DIR, "system-connections"),
                    os.path.join("/", NETWORKMANAGER_DIR, "certs"),
                ],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise Exception(proc.stderr.decode("utf-8"))

            if not os.path.isfile(archive_download_path):
                raise Exception("archive generation failed")

            return (True, "", archive_download_path)
        except Exception as e:
            msg = f"Unable to export connections - {str(e)}"
            syslog(LOG_ERR, msg)
            result = (False, msg, None)
        return result

    @staticmethod
    def get_cert_or_pac_files(type: str) -> List[str]:
        """Retrieve a list of files of the specified type ('cert' or 'pac')"""
        if type not in ["cert", "pac"]:
            return []

        files = []
        with os.scandir(definition.FILEDIR_DICT.get(type)) as listOfEntries:
            for entry in listOfEntries:
                if entry.is_file():
                    strs = entry.name.split(".")
                    if len(strs) == 2 and strs[1] in definition.FILEFMT_DICT.get(type):
                        files.append(entry.name)
        files.sort()
        return files

    # Since we sometimes return a binary file and sometimes return JSON with the GET endpoint, we
    # can't use the @cherrypy.tools.json_out() decorator here. Therefore, we have to mimick this
    # logic when returning JSON.
    def GET(self, *args, **kwargs):
        result = {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "count": 0,
            "files": [],
        }
        type = kwargs.get("type", None)
        valid = ["cert", "pac", "network"]
        if not type:
            result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_FAIL"]
            result["InfoMsg"] = "no filename provided"
            cherrypy.serving.response.headers["Content-Type"] = "application/json"
            return cherrypy._json.encode(result)
        if type not in valid:
            result["InfoMsg"] = f"type not one of {valid}"
            result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_FAIL"]
            cherrypy.serving.response.headers["Content-Type"] = "application/json"
            return cherrypy._json.encode(result)

        if type == "network":
            password = kwargs.get("password", "")
            if not password or password == "":
                result["InfoMsg"] = "Invalid password"
                cherrypy.serving.response.headers["Content-Type"] = "application/json"
                return cherrypy._json.encode(result)

            success, msg, archive = self.export_connections(password)
            if success:
                obj_file = cherrypy.lib.static.serve_file(
                    archive,
                    "application/x-download",
                    "attachment",
                    "connections.zip",
                )
                os.unlink(archive)
                return obj_file
            else:
                syslog(LOG_ERR, f"Could not export connections - {msg}")
                raise cherrypy.HTTPError(500, f"Could not export connections - {msg}")
        else:
            files = FilesManage.get_cert_or_pac_files(type)
            result["files"] = files
            result["count"] = len(files)
            result["InfoMsg"] = f"{type} files"
        cherrypy.serving.response.headers["Content-Type"] = "application/json"
        return cherrypy._json.encode(result)

    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {"SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}

        type = kwargs.get("type", None)
        valid_types = ["network"]
        if not type or type not in valid_types:
            result["InfoMsg"] = "Invalid file type"
            return result

        archive = kwargs.get("archive", None)
        if not archive:
            result["InfoMsg"] = "Invalid archive"
            return result

        password = kwargs.get("password", "")
        if not password or password == "":
            result["InfoMsg"] = "Invalid password"
            return result

        success, msg = self.import_connections(archive, password)
        if success:
            result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
        else:
            syslog(LOG_ERR, f"Could not import connections - {msg}")
            result["InfoMsg"] = f"Could not import connections - {msg}"

        return result

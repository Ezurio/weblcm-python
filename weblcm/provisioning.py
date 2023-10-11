"""Module to handle provisioning"""

from datetime import datetime
from enum import IntEnum
from subprocess import run
from syslog import LOG_ERR, syslog
import shutil
from threading import Timer
from pathlib import Path
from typing import Optional, Tuple
import cherrypy
from weblcm.utils import ServerConfig, restart_weblcm
from weblcm.definition import (
    DEVICE_CA_CERT_CHAIN_PATH,
    DEVICE_SERVER_KEY_PATH,
    DEVICE_SERVER_CSR_PATH,
    DEVICE_SERVER_CERT_PATH,
    PROVISIONING_DIR,
    PROVISIONING_CA_CERT_CHAIN_PATH,
    PROVISIONING_STATE_FILE_PATH,
    CERT_TEMP_PATH,
    CONFIG_FILE_TEMP_PATH,
    WEBLCM_ERRORS,
)
import openssl_extension

OPENSSL_CERT_DATETIME_FORMAT = "%b %d %H:%M:%S %Y %Z"


class ProvisioningState(IntEnum):
    """Enumeration of provisioning states"""

    UNPROVISIONED = 0
    """No provisioning has been completed"""

    PARTIALLY_PROVISIONED = 1
    """The device key/certificate has been provisioned, but the initial time has not been set"""

    FULLY_PROVISIONED = 2
    """The device has been fully provisioned"""


@cherrypy.expose
class CertificateProvisioning:
    """
    Manage device server key/certificate provisioning
    """

    @staticmethod
    def parse_datetime_from_openssl_str(datetime_str: str) -> datetime:
        """Parse the given OpenSSL format date/time string into a datetime object"""
        if datetime_str is None:
            raise Exception()

        return datetime.strptime(datetime_str, OPENSSL_CERT_DATETIME_FORMAT)

    @staticmethod
    def get_client_cert_validity_period() -> Tuple[datetime, datetime]:
        """
        Retrieve the validity period from the client's certificate using the CherryPy WSGI
        environment.
        """
        if not (
            cherrypy.request.wsgi_environ
            and cherrypy.request.wsgi_environ.get("SSL_CLIENT_VERIFY", "NONE")
            == "SUCCESS"
        ):
            raise Exception("Could not read client certificate validity period")

        return (
            CertificateProvisioning.parse_datetime_from_openssl_str(
                cherrypy.request.wsgi_environ.get("SSL_CLIENT_V_START", None)
            ),
            CertificateProvisioning.parse_datetime_from_openssl_str(
                cherrypy.request.wsgi_environ.get("SSL_CLIENT_V_END", None)
            ),
        )

    @staticmethod
    def get_ca_cert_validity_period() -> Tuple[datetime, datetime]:
        """
        Retrieve the validity period from the CA certificate using OpenSSL.
        """
        ca_cert_path = (
            ServerConfig()
            .get(
                section="global",
                option="server.ssl_certificate_chain",
                fallback=DEVICE_CA_CERT_CHAIN_PATH,
            )
            .strip('"')
        )

        if not Path(ca_cert_path).exists():
            raise Exception(
                "Could not get CA certificate validity period - file not found"
            )

        cert_info = openssl_extension.get_cert_info(ca_cert_path, "")

        return (
            CertificateProvisioning.parse_datetime_from_openssl_str(
                cert_info.get("not_before", None)
            ),
            CertificateProvisioning.parse_datetime_from_openssl_str(
                cert_info.get("not_after", None)
            ),
        )

    @staticmethod
    def get_validity_period() -> Tuple[datetime, datetime]:
        """
        Determine the current valid timestamps for setting the current time first using the client's
        certificate validity period (from the CherryPy WSGI environment), and if that isn't present,
        using the CA certificate's validity period.
        """
        try:
            return CertificateProvisioning.get_client_cert_validity_period()
        except Exception:
            # Couldn't read the validity period from the client certificate, so just continue
            pass

        try:
            return CertificateProvisioning.get_ca_cert_validity_period()
        except Exception:
            # Couldn't read the validity period from the CA certificate, so throw an exception
            raise Exception("Could not get validity period")

    @staticmethod
    def validate_new_timestamp(new_timestamp_usec: int) -> bool:
        """
        Validate the given timestamp against the current validity period.
        """
        if not CertificateProvisioning.provisioning_enabled():
            # Certificate provisioning isn't enabled, so no need to perform any validation on the
            # new timestamp
            return True

        try:
            new_timestamp_dt = datetime.fromtimestamp(new_timestamp_usec / 1000000)
            not_before, not_after = CertificateProvisioning.get_validity_period()
            return new_timestamp_dt > not_before and new_timestamp_dt < not_after
        except Exception as exception:
            syslog(f"Could not validate timestamp - {str(exception)}")
            return False

    @staticmethod
    def time_set_callback():
        """Callback fired when the time is set via REST"""
        if (
            CertificateProvisioning.get_provisioning_state()
            == ProvisioningState.PARTIALLY_PROVISIONED
        ):
            # Flag that the system is now fully provisioned
            CertificateProvisioning.set_provisioning_state(
                ProvisioningState.FULLY_PROVISIONED
            )

            # Trigger a restart of WebLCM to ensure the new SSL configuration takes effect
            Timer(0.1, restart_weblcm).start()

    @staticmethod
    def provisioning_enabled() -> bool:
        """Determine if certificate provisioning is enabled"""
        return ServerConfig().getboolean(
            section="weblcm", option="certificate_provisioning", fallback=False
        )

    @staticmethod
    def get_provisioning_state() -> ProvisioningState:
        """Read current provisioning state"""

        if not CertificateProvisioning.provisioning_enabled():
            # If provisioning isn't enabled, then treat it as if we're fully provisioned
            return ProvisioningState.FULLY_PROVISIONED

        if not Path(PROVISIONING_STATE_FILE_PATH).exists():
            CertificateProvisioning.set_provisioning_state(
                ProvisioningState.UNPROVISIONED
            )
            return ProvisioningState.UNPROVISIONED

        try:
            with open(PROVISIONING_STATE_FILE_PATH, "r") as provisioning_state_file:
                return ProvisioningState(int(provisioning_state_file.read()))
        except Exception as exception:
            syslog(f"Unable to read provisioning state - {str(exception)}")
            return ProvisioningState.UNPROVISIONED

    @staticmethod
    def set_provisioning_state(provisioning_state: ProvisioningState):
        """Update the provisioning state file on disk"""
        Path(PROVISIONING_DIR).mkdir(exist_ok=True)
        with open(PROVISIONING_STATE_FILE_PATH, "w") as provisioning_state_file:
            provisioning_state_file.write(str(int(provisioning_state)))

    @staticmethod
    def generate_key_and_csr(config_file, openssl_key_gen_args: Optional[str] = None):
        """
        Utilize OpenSSL to generate a private key and CSR using the provided configuration file. If
        desired, optional OpenSSL key generation args can be provided.
        """
        # Save the config file to a temporary location
        with open(CONFIG_FILE_TEMP_PATH, "wb") as config_file_on_disk:
            while True:
                data = config_file.file.read(8192)
                if not data:
                    break
                config_file_on_disk.write(data)

        Path(PROVISIONING_DIR).mkdir(exist_ok=True)

        if Path(DEVICE_SERVER_KEY_PATH).exists():
            # Private key has already been generated, remove it
            Path(DEVICE_SERVER_KEY_PATH).unlink()

        if openssl_key_gen_args:
            # Generate the key using the arguments provided
            args = ["openssl"]
            args.extend(openssl_key_gen_args.split(" "))
            proc = run(args=args, capture_output=True)
            if proc.returncode:
                raise Exception(proc.stderr.decode("utf-8"))

            if not Path(DEVICE_SERVER_KEY_PATH).exists():
                raise Exception("Key file not found")

            # Build the args to use the new key
            args = [
                "openssl",
                "req",
                "-new",
                "-key",
                DEVICE_SERVER_KEY_PATH,
                "-out",
                DEVICE_SERVER_CSR_PATH,
                "-config",
                CONFIG_FILE_TEMP_PATH,
            ]
        else:
            # Build the args to generate a key and CSR using the default algorithm (ECDSA with the
            # prime256v1 curve
            args = [
                "openssl",
                "req",
                "-nodes",
                "-newkey",
                "ec",
                "-pkeyopt",
                "ec_paramgen_curve:prime256v1",
                "-keyout",
                DEVICE_SERVER_KEY_PATH,
                "-out",
                DEVICE_SERVER_CSR_PATH,
                "-config",
                CONFIG_FILE_TEMP_PATH,
            ]

        proc = run(args=args, capture_output=True)
        if proc.returncode:
            raise Exception(proc.stderr.decode("utf-8"))

        # Remove the temporary config file
        Path(CONFIG_FILE_TEMP_PATH).unlink(missing_ok=True)

    @staticmethod
    def verify_certificate_against_ca(cert_path: str, ca_cert_path: str) -> bool:
        """Utilize OpenSSL to verify a certificate against a CA certificate"""
        try:
            args = ["openssl", "verify", "-CAfile", ca_cert_path, cert_path]
            proc = run(args=args, capture_output=True)
            if proc.returncode:
                raise Exception(proc.stderr.decode("utf-8"))
            return True
        except Exception as exception:
            syslog(LOG_ERR, f"Error verifying certificate: {str(exception)}")
            return False

    @staticmethod
    def save_certificate_file(certificate_file):
        """
        Save an incoming certificate file as the device's server certificate after verifying it
        against the provisioning CA certificate chain
        """
        # Save the certificate to a temporary location
        with open(CERT_TEMP_PATH, "wb") as cert_on_disk:
            while True:
                data = certificate_file.file.read(8192)
                if not data:
                    break
                cert_on_disk.write(data)

        # Verify the certificate
        if not CertificateProvisioning.verify_certificate_against_ca(
            CERT_TEMP_PATH, PROVISIONING_CA_CERT_CHAIN_PATH
        ):
            raise InvalidCertificateError()

        # Move the certificate to the target path
        Path(PROVISIONING_DIR).mkdir(exist_ok=True)
        shutil.move(CERT_TEMP_PATH, DEVICE_SERVER_CERT_PATH)

        # Flag that the device is now partially provisioned
        CertificateProvisioning.set_provisioning_state(
            ProvisioningState.PARTIALLY_PROVISIONED
        )

    @cherrypy.tools.json_out()
    def GET(self):
        return {
            "SDCERR": WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "state": self.get_provisioning_state(),
        }

    def POST(self, *args, **kwargs):
        try:
            if self.get_provisioning_state() != ProvisioningState.UNPROVISIONED:
                syslog("CertificateProvisioning POST - already provisioned")
                raise cherrypy.HTTPError(400, "Already provisioned")

            config_file = kwargs.get("configFile", None)
            if not config_file:
                syslog("CertificateProvisioning POST - no config file specified")
                raise cherrypy.HTTPError(400, "'configFile' not specified")

            if not config_file.filename.endswith(".cnf"):
                syslog("CertificateProvisioning POST - invalid config file type")
                raise cherrypy.HTTPError(400, "'invalid config file type")

            openssl_key_gen_args = kwargs.get("opensslKeyGenArgs", None)

            self.generate_key_and_csr(
                config_file=config_file, openssl_key_gen_args=openssl_key_gen_args
            )

            if not Path(DEVICE_SERVER_KEY_PATH).exists():
                raise cherrypy.HTTPError(500, "Could not generate private key")

            if not Path(DEVICE_SERVER_CSR_PATH).exists():
                raise cherrypy.HTTPError(500, "Could not generate CSR")

            obj_file = cherrypy.lib.static.serve_file(
                DEVICE_SERVER_CSR_PATH,
                "application/x-download",
                "attachment",
                "dev.csr",
            )
            return obj_file
        except cherrypy.HTTPError as error:
            raise error
        except Exception as exception:
            syslog(f"Couldn't generate key and CSR: {str(exception)}")
            raise cherrypy.HTTPError(500, "Could not generate CSR")
        finally:
            # Remove the temporary config file, if present
            Path(CONFIG_FILE_TEMP_PATH).unlink(missing_ok=True)

    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {"SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}

        if self.get_provisioning_state() != ProvisioningState.UNPROVISIONED:
            syslog("CertificateProvisioning PUT - already provisioned")
            result["InfoMsg"] = "Already provisioned"
            return result

        certificate = kwargs.get("certificate", None)
        if not certificate:
            syslog("CertificateProvisioning PUT - no filename specified")
            result["InfoMsg"] = "No filename specified"
            return result

        if not certificate.filename.endswith(
            ".crt"
        ) and not certificate.filename.endswith(".pem"):
            syslog("CertificateProvisioning PUT - invalid certificate type")
            result["InfoMsg"] = "Invalid certificate type"
            return result

        try:
            # Save the newly uploaded certificate to disk
            self.save_certificate_file(certificate)

            # Trigger a restart of WebLCM to ensure the new SSL configuration takes effect
            Timer(0.1, restart_weblcm).start()

            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
        except InvalidCertificateError:
            result["InfoMsg"] = "Invalid certificate file"
        except Exception as exception:
            syslog(f"Couldn't upload certificate file: {str(exception)}")
            result["InfoMsg"] = "Error uploading certificate file"
        return result


class InvalidCertificateError(Exception):
    """
    Custom error class for when the provided certificate cannot be verified against the provisioning
    CA certificate chain
    """

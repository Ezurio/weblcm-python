"""Module to handle provisioning"""

from enum import IntEnum
from subprocess import run
from syslog import LOG_ERR, syslog
import shutil
from threading import Timer
from pathlib import Path
import configparser
import cherrypy
from weblcm import definition
from weblcm.utils import restart_weblcm
from weblcm.definition import (
    DEVICE_SERVER_KEY_PATH,
    DEVICE_SERVER_CSR_PATH,
    DEVICE_SERVER_CERT_PATH,
    PROVISIONING_DIR,
    PROVISIONING_CA_CERT_CHAIN_PATH,
    PROVISIONING_STATE_FILE_PATH,
    CERT_TEMP_PATH,
)


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
    def get_provisioning_state() -> ProvisioningState:
        """Read current provisioning state"""

        parser = configparser.ConfigParser()
        parser.read(definition.WEBLCM_PYTHON_SERVER_CONF_FILE)

        if not parser.getboolean(
            section="weblcm", option="certificate_provisioning", fallback=False
        ):
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
    def generate_key_and_csr(subject: str):
        """
        Utilize OpenSSL to create a CSR using the provided subject and, if not already present, also
        generate a private key
        """
        args = ["openssl", "req"]
        Path(PROVISIONING_DIR).mkdir(exist_ok=True)
        if Path(DEVICE_SERVER_KEY_PATH).exists():
            # Private key has already been generated
            args.extend(
                [
                    "-new",
                    "-key",
                    DEVICE_SERVER_KEY_PATH,
                    "-out",
                    DEVICE_SERVER_CSR_PATH,
                    "-subj",
                    subject,
                ]
            )
        else:
            # Private key not yet generated
            args.extend(
                [
                    "-nodes",
                    "-newkey",
                    "rsa:2048",
                    "-keyout",
                    DEVICE_SERVER_KEY_PATH,
                    "-out",
                    DEVICE_SERVER_CSR_PATH,
                    "-subj",
                    subject,
                ]
            )

        proc = run(args=args, capture_output=True)
        if proc.returncode:
            raise Exception(proc.stderr.decode("utf-8"))

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
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "state": self.get_provisioning_state(),
        }

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    def POST(self):
        try:
            if self.get_provisioning_state() != ProvisioningState.UNPROVISIONED:
                syslog("CertificateProvisioning POST - already provisioned")
                raise cherrypy.HTTPError(400, "Already provisioned")
            country_name = cherrypy.request.json.get("countryName", "US")
            state_name = cherrypy.request.json.get("stateOrProvinceName", "OH")
            locality_name = cherrypy.request.json.get("localityName", "Akron")
            organization_name = cherrypy.request.json.get(
                "organizationName", "LairdConnectivity"
            )
            organizational_unit_name = cherrypy.request.json.get(
                "organizationalUnitName", "IT"
            )
            common_name = cherrypy.request.json.get("commonName", "Summit")

            subject = (
                f"/C={str(country_name)}"
                f"/ST={str(state_name)}"
                f"/L={str(locality_name)}"
                f"/O={str(organization_name)}"
                f"/OU={str(organizational_unit_name)}"
                f"/CN={str(common_name)}"
            )

            self.generate_key_and_csr(subject=subject)

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

    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {"SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}

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

            result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
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

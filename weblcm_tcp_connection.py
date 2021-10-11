import socket
import threading
from typing import Optional

import cherrypy
import dbus

TCP_PORT_MIN: int = 1000
# Keep away from dynamic ports, 49152 to 65535
TCP_PORT_MAX: int = 49152 - 1

TCP_SOCKET_HOST = "0.0.0.0"

FIREWALLD_TIMEOUT_SECONDS = 20
FIREWALLD_SERVICE_NAME = 'org.fedoraproject.FirewallD1'
FIREWALLD_OBJECT_PATH = '/org/fedoraproject/FirewallD1'
FIREWALLD_ZONE_INTERFACE = 'org.fedoraproject.FirewallD1.zone'
FIREWALLD_ZONE = 'internal'


class TcpConnection(object):
    """Represent a TCP server socket connection.
    """

    def __init__(self):
        self._tcp_lock = threading.Lock()
        self._tcp_connection: Optional[socket.socket] = None
        self.port: Optional[int] = None

    @staticmethod
    def validate_port(port: int) -> bool:
        """
        :rtype: bool
        :param port: port number to validate
        :return: true if port falls within valid range; false otherwise
        """
        return TCP_PORT_MIN <= int(port) <= TCP_PORT_MAX

    def tcp_server(self, host, params) -> socket.socket:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = int(params['tcpPort'])
        self.port = port
        server_address = (host, port)
        sock.bind(server_address)
        sock.listen()
        return sock

    def tcp_connection_try_send(self, data_encoded):
        """
        Try to send the supplied data over the tcp connection, ignoring all
        errors, for use in cases where connection may have dropped and
        it is tolerable to not send data.
        :param data_encoded: encoded data to be sent
        :return:
        """
        with self._tcp_lock:
            if self._tcp_connection:
                try:
                    self._tcp_connection.sendall(data_encoded)
                except:
                    pass


def firewalld_open_port(port):
    try:
        bus = dbus.SystemBus()
        bus.call_blocking(bus_name=FIREWALLD_SERVICE_NAME, object_path=FIREWALLD_OBJECT_PATH,
                          dbus_interface=FIREWALLD_ZONE_INTERFACE,
                          method='addPort', signature='sssi', args=[dbus.String(FIREWALLD_ZONE), dbus.String(port),
                                                                    dbus.String('tcp'), dbus.Int32(0)],
                          timeout=FIREWALLD_TIMEOUT_SECONDS)
    except Exception as e:
        cherrypy.log("firewalld_open_port: Exception: " + str(e))


def firewalld_close_port(port):
    try:
        bus = dbus.SystemBus()
        bus.call_blocking(bus_name=FIREWALLD_SERVICE_NAME, object_path=FIREWALLD_OBJECT_PATH,
                          dbus_interface=FIREWALLD_ZONE_INTERFACE,
                          method='removePort', signature='sss', args=[dbus.String(FIREWALLD_ZONE), dbus.String(port),
                                                                      dbus.String('tcp')],
                          timeout=FIREWALLD_TIMEOUT_SECONDS)
    except Exception as e:
        cherrypy.log("firewalld_close_port: Exception: " + str(e))

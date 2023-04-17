from cherrypy.lib.sessions import RamSession
from time import clock_gettime, CLOCK_BOOTTIME
import datetime


class RamBootTimeSession(RamSession):
    def now(self):
        try:
            return datetime.datetime.fromtimestamp(clock_gettime(CLOCK_BOOTTIME))
        except Exception:
            return super().now()

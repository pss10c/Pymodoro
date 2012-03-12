import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from generic_daemon import Daemon
from gi.repository import Gtk
import logging
import traceback
import gobject
import sys

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(threadName)s:%(message)s'
DBUS_BUS_NAME = 'com.pymodoro'
DBUS_DAEMON_PATH = '/com/pymodoro/Daemon'
WORK = 2 ** 0
BREAK = 2 ** 1
LONG_BREAK = BREAK | 2 ** 2
IDLE = 2 ** 3


class PymodoroDaemon(Daemon, dbus.service.Object):
    def __init__(self, pid, work_time=1500, short_break_time=300, long_break_time=900, before_long_break=5):
        Daemon.__init__(self, pid)
        DBusGMainLoop(set_as_default=True)
        self.bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, self.bus_name, DBUS_DAEMON_PATH)
        self._state = IDLE
        self.work_time = work_time
        self.short_break_time = short_break_time
        self.long_break_time = long_break_time
        self.before_long_break = before_long_break
        self.completed = 0
        pass

    def state():
        def fget(self):
            return self._state

        def fset(self, value):
            states = [WORK, BREAK, LONG_BREAK, IDLE]
            if value not in states:
                raise ValueError("Invalid state")
            if self._state == value:
                return

            if self._state & IDLE:
                if value & BREAK:
                    raise ValueError("You must deserve a break")
            self._state = value
            self.state_changed()

        def fdel(self):
            del self._state
        return locals()

    state = property(**state())

    @dbus.service.method(dbus_interface=DBUS_BUS_NAME, out_signature="b")
    def start_pomodoro(self):
        try:
            self.state = WORK
            gobject.timeout_add_seconds(self.work_time, self._work_ended)
            return True
        except ValueError:
            logging.error("Couldn't start pomodoro\n" + traceback.format_exc())
            return False

    def _work_ended(self):
        self.completed += 1
        long_break = False
        if self.completed / self.before_long_break > 0:
            long_break = True
            self.completed = self.completed % self.before_long_break
        self.take_break(long_break=long_break)

    @dbus.service.method(dbus_interface=DBUS_BUS_NAME, out_signature="b")
    def reset_pomodoro(self):
        try:
            self.state = IDLE
            return True
        except ValueError:
            logging.error("Couldn't reset pomodoro\n" + traceback.format_exc())
            return False

    @dbus.service.method(dbus_interface=DBUS_BUS_NAME, out_signature="b")
    def take_break(self, long_break=False):
        try:
            if long_break:
                self.state = LONG_BREAK
                break_time = self.long_break_time
            else:
                self.state = BREAK
                break_time = self.short_break_time
            gobject.timeout_add_seconds(break_time, self._break_ended)
            return True
        except ValueError:
            logging.error(traceback.format_exc())
            return False

    def _break_ended(self):
        self.reset_pomodoro()

    @dbus.service.method(dbus_interface=DBUS_BUS_NAME, out_signature="b")
    def in_work(self):
        return (self.state & WORK) != 0

    @dbus.service.method(dbus_interface=DBUS_BUS_NAME, out_signature="b")
    def in_idle(self):
        return (self.state & IDLE) != 0

    @dbus.service.method(dbus_interface=DBUS_BUS_NAME, out_signature="b")
    def in_break(self):
        return (self.state & BREAK) != 0

    @dbus.service.signal(dbus_interface=DBUS_BUS_NAME)
    def state_changed(self):
        pass

    def run(self):
        Gtk.main()


def main():
    logging.basicConfig(format=LOG_FORMAT, filename='/tmp/pymodoro.log', level=logging.DEBUG)
    action = "start" if len(sys.argv) < 2 else sys.argv[1]
    d = PymodoroDaemon('/tmp/pymodoro.pid')
    if action == "start":
        try:
            d.start()
        except:
            logging.error(traceback.format_exc())
    elif action == "stop":
        d.stop()
    elif action == "restart":
        d.restart()
    else:
        print >> sys.stderr, "Unknown action\nUsage: {start|stop|restart}"

if __name__ == '__main__':
    main()

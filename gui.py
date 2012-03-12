import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gtk
from gi.repository import Notify

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(threadName)s:%(message)s'
DBUS_BUS_NAME = 'com.pymodoro'
DBUS_DAEMON_PATH = '/com/pymodoro/Daemon'
ICON_WORK = '/home/presto/Pictures/pomodoro_small_red.png'
ICON_IDLE = '/home/presto/Pictures/pomodoro_small_grey.png'
ICON_BREAK = '/home/presto/Pictures/pomodoro_small_green.png'


class PymodoroWindow(Gtk.Window):
    def __init__(self, title=""):
        Gtk.Window.__init__(self, title=title)
        self.connect('delete-event', Gtk.main_quit)
        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SessionBus()
        self._daemon = self._bus.get_object(DBUS_BUS_NAME, DBUS_DAEMON_PATH)
        self._daemon_i = dbus.Interface(self._daemon, DBUS_BUS_NAME)
        self._daemon.connect_to_signal('state_changed', self._state_changed_handler)
        Notify.init("Pymodoro")
        self.status_icon = Gtk.StatusIcon.new_from_file(self.get_icon())
        self.status_icon.connect("popup-menu", self._right_click_handler)

        self.menu = Gtk.Menu()
        self.mi_start = Gtk.MenuItem()
        self.mi_start.set_label("Start")

        self.mi_stop = Gtk.MenuItem()
        self.mi_stop.set_label("Interrupt")

        self.mi_quit = Gtk.MenuItem()
        self.mi_quit.set_label("Quit")

        self.mi_start.connect("activate", self._daemon_i.start_pomodoro)
        self.mi_stop.connect("activate", self._daemon_i.reset_pomodoro)
        self.mi_quit.connect("activate", Gtk.main_quit)

        self.menu.append(self.mi_start)
        self.menu.append(self.mi_stop)
        self.menu.append(self.mi_quit)
        self._menu_setup()

    def _menu_setup(self):
        if self._daemon_i.in_work():
            self.mi_start.set_sensitive(False)
            self.mi_stop.set_sensitive(True)
        elif self._daemon_i.in_idle():
            self.mi_start.set_sensitive(True)
            self.mi_stop.set_sensitive(False)
        elif self._daemon_i.in_break():
            self.mi_start.set_sensitive(True)
            self.mi_stop.set_sensitive(False)

    def get_icon(self):
        if self._daemon_i.in_work():
            icon = ICON_WORK
        elif self._daemon_i.in_idle():
            icon = ICON_IDLE
        elif self._daemon_i.in_break():
            icon = ICON_BREAK
        return icon

    def _state_changed_handler(self, sender=None):
        if self._daemon_i.in_work():
            summary = "New pomodoro"
            body = "Have nice work!"
        elif self._daemon_i.in_idle():
            summary = "Ready for new pomodoro?"
            body = "You must work harder!!!"
        elif self._daemon_i.in_break():
            summary = "Take a break"
            body = "Finally. You may take a rest"
        notification = Notify.Notification().new(summary, body, None)
        icon = self.get_icon()
        notification.set_icon_from_pixbuf(Gtk.Image.new_from_file(icon).get_pixbuf())
        notification.show()
        self.status_icon.set_from_file(icon)
        self._menu_setup()

    def _right_click_handler(self, icon, button, time):
        self.menu.show_all()
        self.menu.popup(None, None, lambda menu, icon: Gtk.StatusIcon.position_menu(menu, icon), self.status_icon, button, time)


def main():
    PymodoroWindow()
    Gtk.main()

if __name__ == '__main__':
    main()

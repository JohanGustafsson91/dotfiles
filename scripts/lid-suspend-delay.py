#!/usr/bin/python3
"""Wait fifteen minutes before suspending an undocked laptop with a closed lid."""

import fcntl
import os

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


DELAY_SECONDS = 900
MANAGER = "org.freedesktop.login1.Manager"


def watch_lid():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    proxy = bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")
    manager = dbus.Interface(proxy, MANAGER)
    properties = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
    loop = GLib.MainLoop()
    timer = None
    sleeping = False

    def should_suspend():
        state = properties.GetAll(MANAGER)
        return bool(state["LidClosed"] and not state["Docked"] and not sleeping)

    def suspend():
        nonlocal timer
        timer = None
        if should_suspend():
            print("Lid closed for fifteen minutes; suspending.", flush=True)
            try:
                manager.Suspend(False)
            except dbus.DBusException as error:
                print(f"Suspend failed; restoring system lid handling: {error}", flush=True)
                loop.quit()
        return GLib.SOURCE_REMOVE

    def update_timer():
        nonlocal timer
        if should_suspend():
            if timer is None:
                timer = GLib.timeout_add_seconds(DELAY_SECONDS, suspend)
                print("Lid closed; starting fifteen-minute suspend timer.", flush=True)
        elif timer is not None:
            GLib.source_remove(timer)
            timer = None
            print("Suspend timer cancelled.", flush=True)
        return GLib.SOURCE_CONTINUE

    def properties_changed(interface, changed, invalidated):
        relevant_change = interface == MANAGER and any(
            key in changed or key in invalidated for key in ("LidClosed", "Docked")
        )
        if relevant_change:
            update_timer()

    def prepare_for_sleep(active):
        nonlocal sleeping
        sleeping = bool(active)
        update_timer()

    properties.connect_to_signal("PropertiesChanged", properties_changed)
    manager.connect_to_signal("PrepareForSleep", prepare_for_sleep)

    # Holding this descriptor replaces logind's immediate lid action. Closing
    # it (including on process exit) restores the normal system behaviour.
    inhibitor = manager.Inhibit(
        "handle-lid-switch", "lid-suspend-delay", "Wait fifteen minutes after lid close", "block"
    ).take()
    try:
        update_timer()
        # Docked does not reliably emit PropertiesChanged on logind.
        GLib.timeout_add_seconds(2, update_timer)
        print("Lid delay active (900 seconds).", flush=True)
        loop.run()
    finally:
        os.close(inhibitor)


if __name__ == "__main__":
    lock_path = os.path.join(os.environ["XDG_RUNTIME_DIR"], "lid-suspend-delay.lock")
    with open(lock_path, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(0)
        watch_lid()

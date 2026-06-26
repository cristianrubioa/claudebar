import signal
import sys
import threading

from pystray import Icon

from .acquire import acquire_cookie
from .exceptions import InsecureKeyringError
from .icon import render_icon
from .lock import acquire_lock, release_lock
from .menu import build_menu, start_refresh_thread, start_resume_listener, update_icon
from .state import AppState
from .vault import assert_secure_keyring, save_cookie


def _install_gtk_log_filter():
    try:
        from gi.repository import GLib

        def _handler(log_domain, log_level, message, user_data):
            if "gtk_widget_get_scale_factor" not in (message or ""):
                GLib.log_default_handler(log_domain, log_level, message, user_data)

        GLib.log_set_handler("Gtk", GLib.LogLevelFlags.LEVEL_CRITICAL, _handler, None)
    except Exception:
        pass


def main():
    _install_gtk_log_filter()

    try:
        assert_secure_keyring()
    except InsecureKeyringError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    acquire_lock()

    state = AppState()
    stop_event = threading.Event()

    def on_refresh(icon_obj, item=None):
        state.refresh()
        update_icon(icon_obj, state)

    def _set_cookie(icon_obj, manual):
        cookie = acquire_cookie(manual=manual)
        if cookie:
            save_cookie(cookie)
            state.org_id = None
            state.refresh()
            update_icon(icon_obj, state)

    def on_set_cookie(icon_obj, item=None):
        _set_cookie(icon_obj, manual=False)

    def on_set_cookie_manual(icon_obj, item=None):
        _set_cookie(icon_obj, manual=True)

    def on_quit(icon_obj, item=None):
        stop_event.set()
        icon_obj.stop()

    icon = Icon("claudebar", render_icon())
    icon.on_refresh = on_refresh
    icon.on_set_cookie = on_set_cookie
    icon.on_set_cookie_manual = on_set_cookie_manual
    icon.on_quit = on_quit
    icon.menu = build_menu(state, on_refresh, on_set_cookie, on_set_cookie_manual, on_quit)

    def setup(icon_obj):
        icon_obj.visible = True
        state.refresh()
        update_icon(icon_obj, state)
        start_refresh_thread(state, icon_obj, stop_event)
        start_resume_listener(state, icon_obj)

    def handle_sigterm(signum, frame):
        on_quit(icon)

    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        icon.run(setup=setup)
    finally:
        release_lock()


if __name__ == "__main__":
    main()

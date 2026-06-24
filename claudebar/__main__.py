import signal
import sys
import threading

from pystray import Icon

from .acquire import acquire_cookie
from .exceptions import InsecureKeyringError
from .icon import render_icon
from .lock import acquire_lock, release_lock
from .menu import build_menu, start_refresh_thread, update_icon
from .state import AppState
from .vault import assert_secure_keyring, save_cookie


def main():
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

    def handle_sigterm(signum, frame):
        on_quit(icon)

    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        icon.run(setup=setup)
    finally:
        release_lock()


if __name__ == "__main__":
    main()

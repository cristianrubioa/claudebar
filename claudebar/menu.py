import threading
from datetime import datetime, timezone

from pystray import Menu, MenuItem

from .config import REFRESH_INTERVAL_SECONDS
from .enums import ErrorKind
from .icon import format_label, render_icon
from .vault import load_cookie

_LABEL_GUIDE = "100%"

_BAR_WIDTH = 10


def _progress_bar(util):
    filled = round(min(100, max(0, util)) / 100 * _BAR_WIDTH)
    return "█" * filled + "░" * (_BAR_WIDTH - filled)


def _format_countdown(resets_at):
    delta = resets_at - datetime.now(timezone.utc)
    total_minutes = max(0, int(delta.total_seconds() // 60))
    if total_minutes == 0:
        return "Resets now"
    hours, minutes = divmod(total_minutes, 60)
    if hours == 0:
        return f"Resets in {minutes} min"
    return f"Resets in {hours} hr {minutes} min"


def _format_weekday_time(resets_at):
    local = resets_at.astimezone()
    time_str = local.strftime("%I:%M %p").lstrip("0")
    return f"Resets {local.strftime('%a')} {time_str}"


def _format_window(util, resets_at, reset_format):
    if util is None:
        return "No data"
    bar = _progress_bar(util)
    pct = f"{util:.0f}%"
    if resets_at:
        return f"{bar} {pct} - {reset_format(resets_at)}"
    return f"{bar} {pct}"


def build_menu(state, on_refresh, on_set_cookie, on_set_cookie_manual, on_quit):
    cookie = load_cookie()

    if not cookie:
        items = [MenuItem("No cookie configured", None, enabled=False)]
    elif state.error == ErrorKind.AUTH:
        items = [MenuItem("Cookie expired", None, enabled=False)]
    elif state.error == ErrorKind.CONNECTION:
        items = [MenuItem("Connection error", None, enabled=False)]
    elif state.error == ErrorKind.PARSE:
        items = [MenuItem("Couldn't read usage data", None, enabled=False)]
    elif state.snapshot:
        snap = state.snapshot
        items = [
            MenuItem(
                f"Current Session: {_format_window(snap['session_util'], snap['session_resets_at'], _format_countdown)}",
                None,
                enabled=False,
            ),
            MenuItem(
                f"Weekly: {_format_window(snap['weekly_util'], snap['weekly_resets_at'], _format_weekday_time)}",
                None,
                enabled=False,
            ),
        ]
    else:
        items = [MenuItem("Loading...", None, enabled=False)]

    items += [
        Menu.SEPARATOR,
        MenuItem("Refresh", on_refresh),
        MenuItem("Set Cookie...", on_set_cookie),
        MenuItem("Set Cookie (manual)...", on_set_cookie_manual),
        Menu.SEPARATOR,
        MenuItem("Quit", on_quit),
    ]
    return Menu(*items)


def start_refresh_thread(state, icon, stop_event):
    def loop():
        while not stop_event.is_set():
            state.refresh()
            update_icon(icon, state)
            stop_event.wait(REFRESH_INTERVAL_SECONDS)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread


def _set_native_label(icon, text):
    """Sets the tray's native indicator label (rendered by the host panel
    next to the icon, outside its square bitmap slot). No-ops on backends
    that don't expose this (e.g. anything but pystray's AppIndicator backend)."""
    appindicator = getattr(icon, "_appindicator", None)
    if appindicator is None:
        return
    try:
        from gi.repository import GLib

        def _apply():
            try:
                appindicator.set_label(text, _LABEL_GUIDE)
            except AttributeError:
                pass
            return False

        GLib.idle_add(_apply)
    except ImportError:
        try:
            appindicator.set_label(text, _LABEL_GUIDE)
        except AttributeError:
            pass


def update_icon(icon, state):
    if state.error:
        percent, error = None, True
    elif state.snapshot:
        percent, error = state.snapshot["session_util"], False
    else:
        percent, error = None, False

    icon.icon = render_icon(percent=percent, error=error)
    _set_native_label(icon, format_label(percent, error))
    icon.menu = build_menu(state, icon.on_refresh, icon.on_set_cookie, icon.on_set_cookie_manual, icon.on_quit)
    icon.update_menu()


def _make_wake_handler(icon, state):
    """Builds a D-Bus signal callback that re-renders the cached icon/label
    when the received boolean signals "no longer suspended/locked" (False),
    and ignores the "now suspending/locking" (True) case."""

    def handler(connection, sender_name, object_path, interface_name, signal_name, parameters):
        (still_inactive,) = parameters.unpack()
        if not still_inactive:
            update_icon(icon, state)

    return handler


def start_resume_listener(state, icon):
    """Subscribes to D-Bus suspend/resume and screen lock/unlock signals so
    the native label is re-rendered from the cached snapshot immediately,
    instead of waiting for the next periodic refresh tick. No-ops on tray
    backends without a native label (anything but AppIndicator)."""
    if getattr(icon, "_appindicator", None) is None:
        return

    try:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio
    except (ImportError, ValueError):
        return

    handler = _make_wake_handler(icon, state)

    try:
        system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        system_bus.signal_subscribe(
            "org.freedesktop.login1",
            "org.freedesktop.login1.Manager",
            "PrepareForSleep",
            "/org/freedesktop/login1",
            None,
            Gio.DBusSignalFlags.NONE,
            handler,
        )
    except Exception:
        pass

    try:
        session_bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        # GNOME emits ActiveChanged on org.gnome.ScreenSaver rather than the
        # freedesktop interface; subscribe to both since it varies by DE.
        for interface_name in ("org.freedesktop.ScreenSaver", "org.gnome.ScreenSaver"):
            session_bus.signal_subscribe(
                None,
                interface_name,
                "ActiveChanged",
                None,
                None,
                Gio.DBusSignalFlags.NONE,
                handler,
            )
    except Exception:
        pass

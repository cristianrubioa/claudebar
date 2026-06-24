import threading
from datetime import datetime, timezone

from pystray import Menu, MenuItem

from .config import REFRESH_INTERVAL_SECONDS
from .enums import ErrorKind
from .icon import render_icon
from .vault import load_cookie

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


def update_icon(icon, state):
    if state.error:
        icon.icon = render_icon(percent=None, error=True)
    elif state.snapshot:
        icon.icon = render_icon(percent=state.snapshot["session_util"])
    else:
        icon.icon = render_icon(percent=None, error=False)
    icon.menu = build_menu(state, icon.on_refresh, icon.on_set_cookie, icon.on_set_cookie_manual, icon.on_quit)
    icon.update_menu()

from .enums import WindowKind
from .timeparse import parse_iso8601

SESSION_KEYS = ["five_hour", "session", "current_session"]
WEEKLY_KEYS = ["seven_day", "weekly", "week"]
UTIL_KEYS = ["utilization", "percentage", "percent", "pct"]
RESET_KEYS = ["resets_at", "reset_at", "resetsAt", "resets", "expires_at"]

_WINDOW_KEYS = {
    WindowKind.SESSION: SESSION_KEYS,
    WindowKind.WEEKLY: WEEKLY_KEYS,
}


def extract_cookie_value(name, cookie_str):
    """Extracts a single cookie value (e.g. lastActiveOrg) from a raw Cookie header string."""
    if not cookie_str:
        return None
    for part in cookie_str.split(";"):
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        if key.strip() == name:
            val = val.strip()
            return val or None
    return None


def _first_present(d, keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _parse_window(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return {"utilization": max(0, value), "resets_at": None}
    if not isinstance(value, dict):
        return None
    util = _first_present(value, UTIL_KEYS)
    resets_at = _first_present(value, RESET_KEYS)
    return {
        "utilization": max(0, util) if isinstance(util, (int, float)) else None,
        "resets_at": parse_iso8601(resets_at),
    }


def parse_usage_response(data):
    """Parses the usage endpoint JSON, tolerating multiple known key spellings.

    Returns None if neither the session nor weekly window can be recognized.
    """
    if not isinstance(data, dict):
        return None

    windows = {kind: _parse_window(_first_present(data, keys)) for kind, keys in _WINDOW_KEYS.items()}

    if windows[WindowKind.SESSION] is None and windows[WindowKind.WEEKLY] is None:
        return None

    session = windows[WindowKind.SESSION]
    weekly = windows[WindowKind.WEEKLY]
    return {
        "session_util": session["utilization"] if session else None,
        "session_resets_at": session["resets_at"] if session else None,
        "weekly_util": weekly["utilization"] if weekly else None,
        "weekly_resets_at": weekly["resets_at"] if weekly else None,
    }

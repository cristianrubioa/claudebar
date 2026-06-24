import re
from datetime import datetime, timezone

_FRACTION_RE = re.compile(r"\.(\d+)")


def parse_iso8601(value):
    """Parses an ISO8601 timestamp, tolerating fractional seconds beyond 6 digits."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        secs = value / 1000 if value > 1_000_000_000_000 else value
        return datetime.fromtimestamp(secs, tz=timezone.utc)
    if not isinstance(value, str):
        return None

    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    match = _FRACTION_RE.search(s)
    if match and len(match.group(1)) > 6:
        s = s[: match.start(1)] + match.group(1)[:6] + s[match.end(1) :]

    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None

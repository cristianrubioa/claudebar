from claudebar.usage import extract_cookie_value, parse_usage_response


def test_extracts_value():
    cookie = "sessionKey=abc123; lastActiveOrg=org-1; other=x"
    assert extract_cookie_value("lastActiveOrg", cookie) == "org-1"


def test_missing_key_returns_none():
    cookie = "sessionKey=abc123"
    assert extract_cookie_value("lastActiveOrg", cookie) is None


def test_empty_cookie_returns_none():
    assert extract_cookie_value("lastActiveOrg", "") is None
    assert extract_cookie_value("lastActiveOrg", None) is None


def test_canonical_keys():
    data = {
        "five_hour": {"utilization": 42, "resets_at": "2026-06-13T07:09:59+00:00"},
        "seven_day": {"utilization": 10, "resets_at": "2026-06-20T07:09:59+00:00"},
    }
    snap = parse_usage_response(data)
    assert snap["session_util"] == 42
    assert snap["weekly_util"] == 10
    assert snap["session_resets_at"] is not None


def test_alternate_window_keys():
    data = {
        "current_session": {"percent": 55, "reset_at": "2026-06-13T07:09:59+00:00"},
        "weekly": {"pct": 5, "resetsAt": "2026-06-20T07:09:59+00:00"},
    }
    snap = parse_usage_response(data)
    assert snap["session_util"] == 55
    assert snap["weekly_util"] == 5


def test_unrecognized_schema_returns_none():
    assert parse_usage_response({"totally_unknown": 1}) is None


def test_non_dict_returns_none():
    assert parse_usage_response([1, 2, 3]) is None


def test_session_only():
    data = {"session": {"utilization": 30, "resets_at": None}}
    snap = parse_usage_response(data)
    assert snap["session_util"] == 30
    assert snap["weekly_util"] is None

from datetime import datetime, timezone

from claudebar.timeparse import parse_iso8601


def test_standard_iso8601():
    result = parse_iso8601("2026-06-13T07:09:59+00:00")
    assert result == datetime(2026, 6, 13, 7, 9, 59, tzinfo=timezone.utc)


def test_extended_fractional_seconds():
    result = parse_iso8601("2026-06-13T07:09:59.464637+00:00")
    assert result == datetime(2026, 6, 13, 7, 9, 59, 464637, tzinfo=timezone.utc)


def test_z_suffix():
    result = parse_iso8601("2026-06-13T07:09:59Z")
    assert result == datetime(2026, 6, 13, 7, 9, 59, tzinfo=timezone.utc)


def test_invalid_string_returns_none():
    assert parse_iso8601("not-a-date") is None


def test_none_returns_none():
    assert parse_iso8601(None) is None


def test_epoch_seconds():
    result = parse_iso8601(1750000000)
    assert result == datetime.fromtimestamp(1750000000, tz=timezone.utc)

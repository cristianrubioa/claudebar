import sys
import types
from unittest.mock import Mock

from claudebar.menu import _make_wake_handler, start_resume_listener


class _FakeParameters:
    def __init__(self, value):
        self._value = value

    def unpack(self):
        return (self._value,)


def test_wake_handler_renders_on_resume(monkeypatch):
    update_icon_mock = Mock()
    monkeypatch.setattr("claudebar.menu.update_icon", update_icon_mock)

    icon, state = object(), object()
    handler = _make_wake_handler(icon, state)
    handler(None, None, None, None, "PrepareForSleep", _FakeParameters(False))

    update_icon_mock.assert_called_once_with(icon, state)


def test_wake_handler_renders_on_unlock(monkeypatch):
    update_icon_mock = Mock()
    monkeypatch.setattr("claudebar.menu.update_icon", update_icon_mock)

    icon, state = object(), object()
    handler = _make_wake_handler(icon, state)
    handler(None, None, None, None, "ActiveChanged", _FakeParameters(False))

    update_icon_mock.assert_called_once_with(icon, state)


def test_wake_handler_ignores_suspending_or_locking(monkeypatch):
    update_icon_mock = Mock()
    monkeypatch.setattr("claudebar.menu.update_icon", update_icon_mock)

    icon, state = object(), object()
    handler = _make_wake_handler(icon, state)
    handler(None, None, None, None, "PrepareForSleep", _FakeParameters(True))

    update_icon_mock.assert_not_called()


def test_start_resume_listener_skips_without_appindicator(monkeypatch):
    fake_gi = types.ModuleType("gi")
    fake_gi.require_version = Mock(side_effect=AssertionError("gi should not be imported"))
    monkeypatch.setitem(sys.modules, "gi", fake_gi)

    icon = Mock(spec=[])
    start_resume_listener(state=object(), icon=icon)

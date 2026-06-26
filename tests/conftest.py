import sys
import types
from unittest.mock import MagicMock, sentinel

# pystray connects to the X display at import time; stub it out before any
# test module is collected so headless CI environments don't fail on that.
_fake_pystray = types.ModuleType("pystray")
_fake_pystray.MenuItem = MagicMock()
_fake_menu_cls = MagicMock()
_fake_menu_cls.SEPARATOR = sentinel.SEPARATOR
_fake_pystray.Menu = _fake_menu_cls
sys.modules.setdefault("pystray", _fake_pystray)

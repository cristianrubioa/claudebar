import threading

from .client import fetch_usage, new_session
from .enums import ErrorKind
from .exceptions import AuthError, ConnectionFailure, ParseError
from .vault import load_cookie


class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        self.snapshot = None
        self.error = None  # ErrorKind or None
        self.org_id = None
        self.http = new_session()

    def refresh(self):
        """Performs a fetch under the shared lock, updating snapshot/error state."""
        with self.lock:
            cookie = load_cookie()
            if not cookie:
                self.snapshot = None
                self.error = None
                return
            try:
                snapshot, org_id = fetch_usage(self.http, cookie, self.org_id)
            except AuthError:
                self.error = ErrorKind.AUTH
            except ConnectionFailure:
                self.error = ErrorKind.CONNECTION
            except ParseError:
                self.error = ErrorKind.PARSE
            else:
                self.snapshot = snapshot
                self.org_id = org_id
                self.error = None

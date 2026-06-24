import keyring

from .config import KEYRING_ACCOUNT, KEYRING_SERVICE
from .exceptions import InsecureKeyringError


def assert_secure_keyring():
    """Raises InsecureKeyringError if no secure OS keyring backend is available."""
    backend = keyring.get_keyring()
    module = type(backend).__module__
    if module.startswith("keyring.backends.fail") or module.startswith("keyrings.alt"):
        raise InsecureKeyringError(
            f"No secure keyring backend available (got {type(backend).__name__}). "
            "Install gnome-keyring (GNOME) or kwallet (KDE) and ensure a desktop "
            "session is running, then restart claudebar."
        )


def save_cookie(value):
    assert_secure_keyring()
    keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, value)


def load_cookie():
    assert_secure_keyring()
    return keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)

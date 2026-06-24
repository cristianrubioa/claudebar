import os
import sys

from .config import APP_NAME, CACHE_DIR, PID_FILE


def _pid_is_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def acquire_lock():
    """Acquires the single-instance PID lock, exiting if another instance is alive."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            content = f.read().strip()
        if content.isdigit() and _pid_is_alive(int(content)):
            print(f"{APP_NAME} is already running (PID {content}).", file=sys.stderr)
            sys.exit(1)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$HOME/.config/autostart/claudebar.desktop"
PID_FILE="$HOME/.cache/claudebar/claudebar.pid"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo "Removed autostart entry: $DESKTOP_FILE"
fi

if [ -f "$PID_FILE" ]; then
    rm -f "$PID_FILE"
    echo "Removed lockfile: $PID_FILE"
fi

PYTHON_BIN="python3"
if [ -x "$VENV_DIR/bin/python3" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python3"
fi

"$PYTHON_BIN" - <<'PYEOF'
import keyring

SERVICE = "com.claudebar.cookie"
ACCOUNT = "claude-session-cookie"

try:
    keyring.delete_password(SERVICE, ACCOUNT)
    print("Removed stored cookie from keyring.")
except keyring.errors.PasswordDeleteError:
    print("No stored cookie found in keyring.")
except Exception as exc:
    print(f"Could not access keyring: {exc}")
PYEOF

if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "Removed virtual environment: $VENV_DIR"
fi

echo "claudebar uninstalled."

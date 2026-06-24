#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/claudebar.desktop"
VENV_DIR="$SCRIPT_DIR/.venv"

# The system tray icon needs PyGObject (`gi`) to use the AppIndicator backend.
# `gi` is a compiled binding tied to the system Python and is not pip-installable;
# a pyenv/conda/etc. shadowed `python3` on PATH will not have access to it, which
# silently degrades pystray to its broken Xorg fallback (icon shows, clicks do nothing).
# We must locate the system Python that actually has `gi`.
find_system_python() {
    for candidate in /usr/bin/python3 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c "import gi" >/dev/null 2>&1; then
                command -v "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

SYSTEM_PYTHON="$(find_system_python || true)"
if [ -z "$SYSTEM_PYTHON" ]; then
    echo "Could not find a Python with PyGObject (gi) installed." >&2
    echo "Install it first, e.g. on Ubuntu/Debian:" >&2
    echo "  sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1" >&2
    exit 1
fi
echo "Using system Python with tray support: $SYSTEM_PYTHON"

if ! command -v poetry >/dev/null 2>&1; then
    echo "Poetry is required but was not found on PATH." >&2
    echo "Install it first: https://python-poetry.org/docs/#installation" >&2
    exit 1
fi

echo "Configuring Poetry to keep the venv in-project, inheriting system site-packages for gi..."
poetry -C "$SCRIPT_DIR" config --local virtualenvs.in-project true
poetry -C "$SCRIPT_DIR" config --local virtualenvs.options.system-site-packages true
poetry -C "$SCRIPT_DIR" env use "$SYSTEM_PYTHON" >/dev/null

echo "Installing claudebar dependencies..."
poetry -C "$SCRIPT_DIR" install --only main --no-root

echo "Verifying PyGObject (gi) is reachable from the venv..."
if ! "$VENV_DIR/bin/python3" -c "import gi" >/dev/null 2>&1; then
    echo "gi is not importable from $VENV_DIR even after install." >&2
    echo "Install it first, e.g. on Ubuntu/Debian:" >&2
    echo "  sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1" >&2
    exit 1
fi

mkdir -p "$AUTOSTART_DIR"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=claudebar
Comment=Shows claude.ai usage limits in the system tray
Exec=$VENV_DIR/bin/python3 -m claudebar
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo "Autostart entry written to $DESKTOP_FILE"
echo ""
echo "claudebar will start automatically at your next login."
echo "To launch it now, run:"
echo "  cd $SCRIPT_DIR && $VENV_DIR/bin/python3 -m claudebar"

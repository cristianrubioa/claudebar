import glob
import os
import shutil
import subprocess

import browser_cookie3

from .config import CLAUDE_DOMAIN

# browser_cookie3 knows the snap-confined path for Firefox but not for
# Chromium-based browsers, even though Chromium ships only as a snap on
# Ubuntu and Brave is also commonly installed that way. Glob for their
# snap data dirs explicitly and decrypt via the matching browser_cookie3
# class (decryption itself still goes through the OS keyring as usual).
_SNAP_COOKIE_PATTERNS = [
    (browser_cookie3.brave, "~/snap/brave/*/.config/BraveSoftware/Brave-Browser/Default/Cookies"),
    (browser_cookie3.brave, "~/snap/brave/*/.config/BraveSoftware/Brave-Browser/Profile */Cookies"),
    (browser_cookie3.chromium, "~/snap/chromium/common/chromium/Default/Cookies"),
    (browser_cookie3.chromium, "~/snap/chromium/common/chromium/Profile */Cookies"),
    (browser_cookie3.chrome, "~/snap/google-chrome/*/.config/google-chrome/Default/Cookies"),
]


def _snap_cookie_jars(domain_name):
    for factory, pattern in _SNAP_COOKIE_PATTERNS:
        paths = sorted(glob.glob(os.path.expanduser(pattern)), key=os.path.getmtime, reverse=True)
        for path in paths:
            try:
                yield factory(cookie_file=path, domain_name=domain_name)
            except Exception:
                continue


def auto_detect_cookie():
    """Tries to read a usable claude.ai session cookie out of installed browsers.

    Returns the assembled Cookie header string, or None if no browser yielded
    a cookie jar containing sessionKey.
    """
    jars = []
    try:
        jars.append(browser_cookie3.load(domain_name=CLAUDE_DOMAIN))
    except Exception:
        pass
    jars.extend(_snap_cookie_jars(CLAUDE_DOMAIN))

    for jar in jars:
        cookies = {c.name: c.value for c in jar}
        if "sessionKey" in cookies:
            return "; ".join(f"{name}={value}" for name, value in cookies.items())
    return None


def prompt_for_cookie():
    """Prompts the user to paste their cookie via zenity, falling back to stdin."""
    if shutil.which("zenity"):
        result = subprocess.run(
            [
                "zenity",
                "--entry",
                "--width=600",
                "--title=claudebar",
                "--text=Paste your claude.ai Cookie header value:",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
        return None

    print("zenity not found. Paste your claude.ai Cookie header value below.")
    try:
        return input("Cookie: ").strip() or None
    except EOFError:
        return None


def acquire_cookie(manual=False):
    """Acquires a cookie: auto-detected from a browser, unless manual entry is requested."""
    if not manual:
        detected = auto_detect_cookie()
        if detected:
            return detected
    return prompt_for_cookie()

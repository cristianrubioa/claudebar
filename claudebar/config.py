import os

APP_NAME = "claudebar"
KEYRING_SERVICE = "com.claudebar.cookie"
KEYRING_ACCOUNT = "claude-session-cookie"

CACHE_DIR = os.path.expanduser(f"~/.cache/{APP_NAME}")
PID_FILE = os.path.join(CACHE_DIR, f"{APP_NAME}.pid")

CLAUDE_DOMAIN = "claude.ai"
USAGE_URL_TEMPLATE = "https://claude.ai/api/organizations/{org}/usage"
ORGANIZATIONS_URL = "https://claude.ai/api/organizations"
REFERER = "https://claude.ai/settings/usage"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

REFRESH_INTERVAL_SECONDS = 300

THRESHOLD_YELLOW = 80
THRESHOLD_RED = 90

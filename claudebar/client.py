from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestException

from .config import ORGANIZATIONS_URL, REFERER, USAGE_URL_TEMPLATE, USER_AGENT
from .exceptions import AuthError, ConnectionFailure, ParseError
from .usage import extract_cookie_value, parse_usage_response


def _headers(cookie):
    return {
        "Cookie": cookie,
        "User-Agent": USER_AGENT,
        "Referer": REFERER,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _is_cloudflare_challenge(resp):
    """Detects a Cloudflare bot-challenge response, distinct from a genuine API auth error."""
    if "cf-mitigated" in resp.headers:
        return True
    return "text/html" in resp.headers.get("Content-Type", "")


def _get(session, url, cookie, timeout=20):
    try:
        resp = session.get(url, headers=_headers(cookie), timeout=timeout, impersonate="chrome")
    except RequestException as exc:
        raise ConnectionFailure(str(exc)) from exc
    if resp.status_code in (401, 403):
        if _is_cloudflare_challenge(resp):
            raise ConnectionFailure(f"Blocked by Cloudflare (HTTP {resp.status_code})")
        raise AuthError(f"HTTP {resp.status_code}")
    return resp


def resolve_org(session, cookie):
    """Calls GET /api/organizations and selects lastActiveOrg, falling back to the first org."""
    resp = _get(session, ORGANIZATIONS_URL, cookie)
    if resp.status_code != 200:
        raise ParseError(f"HTTP {resp.status_code} from /api/organizations")
    try:
        orgs = resp.json()
    except ValueError as exc:
        raise ParseError("Unexpected /api/organizations response") from exc
    if not isinstance(orgs, list) or not orgs:
        raise ParseError("No organizations returned")

    preferred = extract_cookie_value("lastActiveOrg", cookie)
    chosen = next((o for o in orgs if o.get("uuid") == preferred), orgs[0])
    org_id = chosen.get("uuid")
    if not org_id:
        raise ParseError("Organization response missing uuid")
    return org_id


def fetch_usage(session, cookie, org_id=None):
    """Fetches and parses usage data, resolving the organization id as needed.

    Returns (snapshot_dict, resolved_org_id).
    """
    resolved_org = org_id or extract_cookie_value("lastActiveOrg", cookie)
    if resolved_org is None:
        resolved_org = resolve_org(session, cookie)

    resp = _get(session, USAGE_URL_TEMPLATE.format(org=resolved_org), cookie)

    if resp.status_code == 404:
        resolved_org = resolve_org(session, cookie)
        resp = _get(session, USAGE_URL_TEMPLATE.format(org=resolved_org), cookie)

    if resp.status_code != 200:
        raise ParseError(f"HTTP {resp.status_code} from usage endpoint")

    try:
        data = resp.json()
    except ValueError as exc:
        raise ParseError("Usage response was not valid JSON") from exc

    snapshot = parse_usage_response(data)
    if snapshot is None:
        raise ParseError("Usage response did not match any known schema")

    return snapshot, resolved_org


def new_session():
    return requests.Session()

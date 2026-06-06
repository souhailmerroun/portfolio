"""
Get or set cookies in the browser context.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._cdp import run_node


def pw_cookies(url: str = None, set_cookie: str = None, cdp_url: str = "http://localhost:9222") -> dict:
    """
    Get cookies for a URL, or set a cookie.

    To get cookies: call with just url (or no args for all cookies).
    To set a cookie: pass set_cookie as a JSON string like '{"name": "token", "value": "abc123", "domain": ".example.com", "path": "/"}'

    Args:
        url: URL to filter cookies for (optional, returns all cookies if omitted)
        set_cookie: JSON string of a cookie to set (optional). Must include at least "name", "value", and "url" or "domain".
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - cookies: List of cookies (when getting)
        - set: The cookie that was set (when setting)
        - error: Error message if failed
    """
    if set_cookie:
        # Setting a cookie
        try:
            cookie_obj = json.loads(set_cookie)
        except json.JSONDecodeError:
            return {"status": "error", "error": "set_cookie must be valid JSON"}

        cookie_json = json.dumps(cookie_obj)
        script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        const cookie = {cookie_json};
        await context.addCookies([cookie]);
        console.log(JSON.stringify({{
            status: 'ok',
            set: cookie
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    else:
        # Getting cookies
        if url:
            safe_url = url.replace("'", "\\'")
            cookies_code = f"const cookies = await context.cookies('{safe_url}');"
        else:
            cookies_code = "const cookies = await context.cookies();"

        script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {cookies_code}
        console.log(JSON.stringify({{
            status: 'ok',
            cookies: cookies,
            count: cookies.length
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=15, err_timeout="Cookies operation timed out")

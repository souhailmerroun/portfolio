"""
Navigate to a URL in the browser.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_goto(url: str, page_index: int = None, wait_until: str = "domcontentloaded", cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Navigate to a URL in an open browser tab.

    Args:
        url: The URL to navigate to (e.g., "https://google.com")
        page_index: Which tab to use, by index. REQUIRED unless page_url is given — there is NO default (tab 0 is the user's active tab; never hijack it). Get the index from pw_list_tabs.
        wait_until: When to consider navigation done - "domcontentloaded", "load", or "networkidle" (default: "domcontentloaded")
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - url: The final URL after navigation (may differ due to redirects)
        - title: The page title after navigation
        - error: Error message if failed
    """
    safe_url = url.replace("'", "\\'")
    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.goto('{safe_url}', {{ waitUntil: '{wait_until}', timeout: 30000 }});
        console.log(JSON.stringify({{
            status: 'ok',
            url: page.url(),
            title: await page.title()
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=45, err_timeout="Navigation timed out")

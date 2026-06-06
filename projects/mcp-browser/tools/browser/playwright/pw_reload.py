"""
Reload the current page.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_reload(page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Reload the current page.

    Args:
        page_index: Which tab to reload, by index (REQUIRED unless page_url given; no default — tab 0 is the user's tab)
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - url: The page URL after reload
        - title: The page title after reload
        - error: Error message if failed
    """
    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.reload({{ waitUntil: 'domcontentloaded', timeout: 30000 }});
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
    return run_node(script, timeout=45, err_timeout="Reload timed out")

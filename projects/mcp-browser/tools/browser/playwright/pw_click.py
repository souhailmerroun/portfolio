"""
Click an element on the page.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_click(selector: str, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Click an element on the page using a CSS selector.

    Args:
        selector: CSS selector of the element to click (e.g., "button.submit", "#login", "a[href='/about']")
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - selector: The selector that was clicked
        - url: The page URL after clicking (may change if navigation occurred)
        - error: Error message if failed
    """
    safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.click('{safe_selector}', {{ timeout: 10000 }});
        await page.waitForTimeout(500);
        console.log(JSON.stringify({{
            status: 'ok',
            selector: '{safe_selector}',
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
    return run_node(script, timeout=30, err_timeout="Click timed out")

"""
Fill a form field (clears existing value first, then sets the new value instantly).
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_fill(selector: str, value: str, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Fill a form field by clearing it and setting a new value instantly.

    Unlike pw_type, this does not simulate key-by-key input. It clears the field
    and sets the value directly. Use this for simple form filling.

    Args:
        selector: CSS selector of the input element (e.g., "input[name='email']", "#search")
        value: The value to fill in
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - selector: The selector that was filled
        - value: The value that was set
        - error: Error message if failed
    """
    safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
    safe_value = value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.fill('{safe_selector}', '{safe_value}', {{ timeout: 10000 }});
        console.log(JSON.stringify({{
            status: 'ok',
            selector: '{safe_selector}',
            value: '{safe_value}'
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=30, err_timeout="Fill timed out")

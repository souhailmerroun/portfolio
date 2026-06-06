"""
Type text into a focused element or selector, key by key (simulates real typing).
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_type(text: str, selector: str = None, delay: int = 50, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Type text into an element, simulating real key-by-key input.

    If no selector is given, types into the currently focused element.
    Use this when you need realistic typing (e.g., triggering autocomplete).
    Use pw_fill instead for simply setting an input value.

    Args:
        text: The text to type
        selector: CSS selector of the input element (optional, types into focused element if omitted)
        delay: Delay in milliseconds between keystrokes (default: 50)
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - text: The text that was typed
        - error: Error message if failed
    """
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    if selector:
        safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
        type_code = f"await page.locator('{safe_selector}').type('{safe_text}', {{ delay: {delay} }});"
    else:
        type_code = f"await page.keyboard.type('{safe_text}', {{ delay: {delay} }});"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        {type_code}
        console.log(JSON.stringify({{
            status: 'ok',
            text: '{safe_text}'
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=60, err_timeout="Typing timed out")

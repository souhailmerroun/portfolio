"""
Press a keyboard key or key combination.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_press(key: str, selector: str = None, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Press a keyboard key or key combination.

    Args:
        key: Key to press. Examples: "Enter", "Tab", "Escape", "Backspace", "ArrowDown",
             "Control+a", "Meta+c" (Cmd+C on Mac), "Shift+Tab", "Control+Shift+k"
        selector: CSS selector to focus before pressing (optional, presses on current focus if omitted)
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - key: The key that was pressed
        - error: Error message if failed
    """
    safe_key = key.replace("\\", "\\\\").replace("'", "\\'")
    if selector:
        safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
        press_code = f"await page.press('{safe_selector}', '{safe_key}');"
    else:
        press_code = f"await page.keyboard.press('{safe_key}');"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        {press_code}
        console.log(JSON.stringify({{
            status: 'ok',
            key: '{safe_key}'
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=15, err_timeout="Key press timed out")

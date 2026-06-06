"""
Scroll the page or a specific element.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_scroll(direction: str = "down", amount: int = 500, selector: str = None, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Scroll the page or a specific element.

    Args:
        direction: Scroll direction - "up", "down", "left", "right", "top" (scroll to top), or "bottom" (scroll to bottom) (default: "down")
        amount: Pixels to scroll for up/down/left/right (default: 500, ignored for top/bottom)
        selector: CSS selector of a scrollable element (optional, scrolls the page if omitted)
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - direction: The scroll direction used
        - scroll_position: Current scroll position after scrolling (x, y)
        - error: Error message if failed
    """
    if selector:
        safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
        target = f"document.querySelector('{safe_selector}')"
    else:
        target = "window"

    scroll_map = {
        "down": f"{target}.scrollBy(0, {amount})",
        "up": f"{target}.scrollBy(0, -{amount})",
        "right": f"{target}.scrollBy({amount}, 0)",
        "left": f"{target}.scrollBy(-{amount}, 0)",
        "top": f"{target}.scrollTo(0, 0)",
        "bottom": f"{target}.scrollTo(0, document.body.scrollHeight)",
    }
    scroll_code = scroll_map.get(direction, scroll_map["down"])

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.evaluate(() => {{ {scroll_code} }});
        await page.waitForTimeout(300);
        const pos = await page.evaluate(() => ({{ x: window.scrollX, y: window.scrollY }}));
        console.log(JSON.stringify({{
            status: 'ok',
            direction: '{direction}',
            scroll_position: pos
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=15, err_timeout="Scroll timed out")

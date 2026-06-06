"""
Take a screenshot of the current page.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node
from tools.browser.playwright.optimize_screenshot import optimize_screenshot
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")


def pw_screenshot(path: str = None, selector: str = None, full_page: bool = False, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None, optimize: bool = True) -> dict:
    """
    Take a screenshot of the current page or a specific element.

    Args:
        path: File path to save the screenshot (default: ~/Downloads/screenshot.png)
        selector: CSS selector to screenshot a specific element instead of the full viewport
        full_page: Capture the entire scrollable page, not just the viewport (default: false)
        page_index: Which tab to screenshot, by index (REQUIRED unless page_url given; no default — tab 0 is the user's tab)
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")
        optimize: Resize to ≤1568px longest side + JPEG-encode in-place to stay under
            the 2000px per-conversation image limit (default: true). Set false for raw PNG.

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - path: The file path where the screenshot was saved
        - error: Error message if failed
    """
    save_path = path or os.path.join(DOWNLOADS_DIR, "screenshot.png")
    safe_path = save_path.replace("'", "\\'")

    if selector:
        safe_selector = selector.replace("'", "\\'").replace("\\", "\\\\")
        screenshot_code = f"await page.locator('{safe_selector}').screenshot({{ path: '{safe_path}' }});"
    else:
        screenshot_code = f"await page.screenshot({{ path: '{safe_path}', fullPage: {str(full_page).lower()} }});"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        {screenshot_code}
        console.log(JSON.stringify({{
            status: 'ok',
            path: '{safe_path}',
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
    return run_node(script, timeout=30, err_timeout="Screenshot timed out")

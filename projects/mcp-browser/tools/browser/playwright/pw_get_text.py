"""
Extract text content from the page or a specific element.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_get_text(selector: str = None, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Extract text content from the page or a specific element.

    Args:
        selector: CSS selector to extract text from (optional, extracts full page text if omitted)
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - text: The extracted text content (truncated to 50000 chars if very long)
        - length: The full length of the text before truncation
        - error: Error message if failed
    """
    if selector:
        safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
        extract_code = f"const text = await page.locator('{safe_selector}').innerText({{ timeout: 10000 }});"
    else:
        extract_code = "const text = await page.innerText('body');"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        {extract_code}
        const truncated = text.substring(0, 50000);
        console.log(JSON.stringify({{
            status: 'ok',
            text: truncated,
            length: text.length
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=30, err_timeout="Get text timed out")

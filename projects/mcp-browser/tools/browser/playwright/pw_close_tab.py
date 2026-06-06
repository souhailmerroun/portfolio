"""
Close a browser tab by index.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_close_tab(page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Close a browser tab by its index.

    Args:
        page_index: Index of the tab to close — REQUIRED unless page_url is given; no default. Close only YOUR worker tab, never the user's.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - closed_index: The index of the closed tab
        - remaining_tabs: Number of tabs remaining
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
        await page.close();
        console.log(JSON.stringify({{
            status: 'ok',
            closed_index: {page_index},
            remaining_tabs: context.pages().length
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=15, err_timeout="Close tab timed out")

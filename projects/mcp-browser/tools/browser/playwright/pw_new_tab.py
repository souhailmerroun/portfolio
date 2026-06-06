"""
Open a new browser tab, optionally navigating to a URL.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._cdp import run_node


def pw_new_tab(url: str = None, cdp_url: str = "http://localhost:9222") -> dict:
    """
    Open a new browser tab, optionally navigating to a URL.

    Args:
        url: URL to open in the new tab (optional, opens blank tab if omitted)
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - page_index: The index of the newly created tab
        - url: The URL of the new tab
        - title: The title of the new tab
        - total_tabs: Total number of open tabs after creation
        - error: Error message if failed
    """
    if url:
        safe_url = url.replace("'", "\\'")
        goto_code = f"await page.goto('{safe_url}', {{ waitUntil: 'domcontentloaded', timeout: 30000 }});"
    else:
        goto_code = ""

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        const page = await context.newPage();
        {goto_code}
        const allPages = context.pages();
        const pageIndex = allPages.indexOf(page);
        console.log(JSON.stringify({{
            status: 'ok',
            page_index: pageIndex,
            url: page.url(),
            title: await page.title(),
            total_tabs: allPages.length
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=45, err_timeout="New tab timed out")

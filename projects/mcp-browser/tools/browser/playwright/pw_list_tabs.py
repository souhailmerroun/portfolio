"""
List all open browser tabs with their titles and URLs.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._cdp import run_node


def pw_list_tabs(cdp_url: str = "http://localhost:9222") -> dict:
    """
    List all open browser tabs with their index, title, and URL.

    Args:
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - tabs: List of tabs, each with index, title, and url
        - total: Total number of open tabs
        - error: Error message if failed
    """
    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        const pages = context.pages();
        const tabs = [];
        for (let i = 0; i < pages.length; i++) {{
            tabs.push({{
                index: i,
                title: await pages[i].title(),
                url: pages[i].url()
            }});
        }}
        console.log(JSON.stringify({{
            status: 'ok',
            tabs: tabs,
            total: tabs.length
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=15, err_timeout="List tabs timed out")

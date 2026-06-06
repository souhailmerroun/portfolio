"""
Wait for a selector to appear, disappear, or for a timeout.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_wait(page_index: int, selector: str = None, state: str = "visible", timeout: int = 10000, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Wait for a condition on the page.

    Args:
        page_index: Which tab to use, by index. Use resolve_tab(tab_id=...) to convert an Arc tab ID to a page_index.
        selector: CSS selector to wait for (optional, if omitted just waits for the timeout duration)
        state: What state to wait for - "visible", "hidden", "attached", or "detached" (default: "visible")
        timeout: Maximum time to wait in milliseconds (default: 10000)
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - waited_for: Description of what was waited for
        - error: Error message if the wait timed out or failed
    """
    if selector:
        safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
        wait_code = f"await page.waitForSelector('{safe_selector}', {{ state: '{state}', timeout: {timeout} }});"
        waited_desc = f"selector '{selector}' to be {state}"
    else:
        wait_code = f"await page.waitForTimeout({timeout});"
        waited_desc = f"{timeout}ms timeout"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        {wait_code}
        console.log(JSON.stringify({{
            status: 'ok',
            waited_for: `{waited_desc}`
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    subprocess_timeout = (timeout / 1000) + 15  # extra buffer beyond the JS timeout
    return run_node(script, timeout=120, err_timeout="Wait timed out at subprocess level")

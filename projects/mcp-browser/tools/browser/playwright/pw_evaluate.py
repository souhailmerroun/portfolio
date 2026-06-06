"""
Execute arbitrary JavaScript in the page context.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_evaluate(expression: str, page_index: int, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Execute JavaScript in the page context and return the result.

    The expression is evaluated as-is. Return a value to get it back.
    For complex scripts, wrap in an IIFE: "(() => { ... return result; })()"

    Args:
        expression: JavaScript expression to evaluate (e.g., "document.title", "window.location.href", "document.querySelectorAll('a').length")
        page_index: Which tab to use, by index. Use resolve_tab(tab_id=...) to convert an Arc tab ID to a page_index.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - result: The return value of the expression (serialized to JSON)
        - error: Error message if failed
    """
    # Use base64 to safely pass the expression without escaping issues
    import base64
    encoded = base64.b64encode(expression.encode()).decode()

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        const expr = Buffer.from('{encoded}', 'base64').toString('utf8');
        const result = await page.evaluate(expr);
        console.log(JSON.stringify({{
            status: 'ok',
            result: result
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=30, err_timeout="Evaluate timed out")

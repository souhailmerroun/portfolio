"""
Select an option from a dropdown/select element.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_select(selector: str, value: str = None, label: str = None, index: int = None, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Select an option from a <select> dropdown element.

    Provide one of: value, label, or index to identify which option to select.

    Args:
        selector: CSS selector of the <select> element
        value: Option value attribute to select (e.g., "us" for <option value="us">)
        label: Visible text of the option to select (e.g., "United States")
        index: Zero-based index of the option to select
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - selected: The value(s) that were selected
        - error: Error message if failed
    """
    safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")

    if value is not None:
        safe_value = str(value).replace("\\", "\\\\").replace("'", "\\'")
        select_arg = f"{{ value: '{safe_value}' }}"
    elif label is not None:
        safe_label = label.replace("\\", "\\\\").replace("'", "\\'")
        select_arg = f"{{ label: '{safe_label}' }}"
    elif index is not None:
        select_arg = f"{{ index: {index} }}"
    else:
        return {"status": "error", "error": "Provide one of: value, label, or index"}

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        const selected = await page.selectOption('{safe_selector}', {select_arg}, {{ timeout: 10000 }});
        console.log(JSON.stringify({{
            status: 'ok',
            selected: selected
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=30, err_timeout="Select timed out")

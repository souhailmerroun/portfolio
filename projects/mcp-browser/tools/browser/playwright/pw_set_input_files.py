"""
Set files on a file input element, bypassing the native OS file picker.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_set_input_files(selector: str, file_paths: list, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Set files on a file input element without triggering the native OS file picker.

    Args:
        selector: CSS selector of the file input element (e.g., "input[name='files']", "input[type='file']")
        file_paths: List of absolute file paths to set (e.g., ["/Users/me/Downloads/photo.jpg"])
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - selector: The selector used
        - files: The file paths that were set
        - error: Error message if failed
    """
    safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
    files_json = json.dumps(file_paths)

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        const files = {files_json};
        await page.setInputFiles('{safe_selector}', files);
        await page.waitForTimeout(500);
        console.log(JSON.stringify({{
            status: 'ok',
            selector: '{safe_selector}',
            files: files
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=30, err_timeout="setInputFiles timed out")

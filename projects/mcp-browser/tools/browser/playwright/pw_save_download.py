"""
Click an element that triggers a file download and save it to a specified path.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_save_download(selector: str, save_path: str, page_index: int = None, cdp_url: str = "http://localhost:9222", timeout: int = 15000, page_url: str = None) -> dict:
    """
    Click an element that triggers a download and save the file to a specified path.

    Unlike pw_download (which reads content as UTF-8), this tool saves binary files
    correctly — suitable for images, PDFs, etc.

    Args:
        selector: CSS selector of the element that triggers the download
        save_path: Absolute path where the file should be saved (e.g., "/Users/me/Downloads/image.jpg")
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")
        timeout: Maximum time to wait for the download in milliseconds (default: 15000)

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - save_path: The path where the file was saved
        - filename: The suggested filename from the server
        - error: Error message if failed
    """
    safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
    safe_save_path = save_path.replace("\\", "\\\\").replace("'", "\\'")

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}

        const [download] = await Promise.all([
            page.waitForEvent('download', {{ timeout: {timeout} }}),
            page.click('{safe_selector}', {{ timeout: 10000 }})
        ]);

        await download.saveAs('{safe_save_path}');

        console.log(JSON.stringify({{
            status: 'ok',
            save_path: '{safe_save_path}',
            filename: download.suggestedFilename()
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    subprocess_timeout = (timeout / 1000) + 20
    return run_node(script, timeout=60, err_timeout="Download timed out")

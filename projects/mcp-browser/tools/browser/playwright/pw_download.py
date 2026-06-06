"""
Click an element that triggers a file download and return the file content.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_download(selector: str, page_index: int, cdp_url: str = "http://localhost:9222", timeout: int = 15000, page_url: str = None) -> dict:
    """
    Click an element that triggers a download and return the downloaded file content.

    Args:
        selector: CSS selector of the element that triggers the download (e.g., 'button[aria-labelledby="csv_download"]')
        page_index: Which tab to use, by index. Use resolve_tab(tab_id=...) to convert an Arc tab ID to a page_index.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")
        timeout: Maximum time to wait for the download in milliseconds (default: 15000)

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - filename: The suggested filename of the download
        - content: The file content as a string (UTF-8)
        - error: Error message if failed
    """
    safe_selector = selector.replace("\\", "\\\\").replace("'", "\\'")
    script = f"""
const {{ chromium }} = require('playwright');
const path = require('path');
const fs = require('fs');
const os = require('os');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}

        const downloadPromise = page.waitForEvent('download', {{ timeout: {timeout} }});
        await page.click('{safe_selector}', {{ timeout: 10000 }});
        const download = await downloadPromise;

        const tmpPath = path.join(os.tmpdir(), 'pw_download_' + Date.now());
        await download.saveAs(tmpPath);
        const content = fs.readFileSync(tmpPath, 'utf-8');
        fs.unlinkSync(tmpPath);

        console.log(JSON.stringify({{
            status: 'ok',
            filename: download.suggestedFilename(),
            content: content
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

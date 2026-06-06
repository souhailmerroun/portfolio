"""
Save the current page as a PDF file.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")


def pw_pdf(path: str = None, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Save the current page as a PDF file.

    Note: PDF generation only works with headless Chrome. If Chrome was opened
    in headed mode, this will return an error.

    Args:
        path: File path to save the PDF (default: ~/Downloads/page.pdf)
        page_index: Which tab to save as PDF, by index (REQUIRED unless page_url given; no default — tab 0 is the user's tab)
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - path: The file path where the PDF was saved
        - error: Error message if failed
    """
    save_path = path or os.path.join(DOWNLOADS_DIR, "page.pdf")
    safe_path = save_path.replace("'", "\\'")

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.pdf({{
            path: '{safe_path}',
            format: 'A4',
            printBackground: true,
            margin: {{ top: '1cm', right: '1cm', bottom: '1cm', left: '1cm' }}
        }});
        console.log(JSON.stringify({{
            status: 'ok',
            path: '{safe_path}',
            url: page.url(),
            title: await page.title()
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=30, err_timeout="PDF generation timed out")

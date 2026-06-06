"""
Capture console.log output from the page.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_console(duration: int = 10, level: str = "all", page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Capture console output (console.log, errors, warnings) from the page for a given duration.

    Listens to the browser console for the specified duration and returns all captured messages.
    Also captures uncaught page errors.

    Args:
        duration: How many seconds to listen for console output (default: 10)
        level: Filter by log level - "all", "log", "warning", "error", "info", "debug" (default: "all")
        page_index: Which tab to capture from — REQUIRED unless page_url is given; no default (tab 0 is the user's tab). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - messages: List of console messages, each with type (log/warning/error/info/debug), text, and timestamp
        - errors: List of uncaught page errors
        - total: Total number of messages captured
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
        const messages = [];
        const errors = [];
        const startTime = Date.now();

        page.on('console', msg => {{
            const type = msg.type();
            const filter = '{level}';
            if (filter === 'all' || type === filter) {{
                messages.push({{
                    type: type,
                    text: msg.text(),
                    timestamp: Date.now() - startTime,
                    location: msg.location()
                }});
            }}
        }});

        page.on('pageerror', err => {{
            errors.push({{
                message: err.message,
                stack: err.stack,
                timestamp: Date.now() - startTime
            }});
        }});

        await page.waitForTimeout({duration * 1000});

        console.log(JSON.stringify({{
            status: 'ok',
            messages: messages.slice(0, 500),
            errors: errors.slice(0, 100),
            total: messages.length,
            total_errors: errors.length,
            duration_ms: {duration * 1000}
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    subprocess_timeout = duration + 20
    return run_node(script, timeout=60, err_timeout="Console capture timed out")

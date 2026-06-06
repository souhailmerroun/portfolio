"""
Intercept, block, or mock network requests.
"""
import subprocess
import json
import os
import base64

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_intercept(action: str = "log", url_pattern: str = "**/*", mock_body: str = None, mock_status: int = 200, mock_content_type: str = "application/json", duration: int = 10, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Intercept network requests on the page. Can log, block, or mock matching requests.

    Args:
        action: What to do with matching requests - "log" (capture all requests/responses), "block" (abort matching requests), or "mock" (return fake response) (default: "log")
        url_pattern: Glob pattern to match URLs (default: "**/*" for all). Examples: "**/api/**", "**/*.png", "**/graphql"
        mock_body: Response body to return when action is "mock" (e.g., '{"data": []}')
        mock_status: HTTP status code to return when mocking (default: 200)
        mock_content_type: Content-Type header for mock response (default: "application/json")
        duration: How many seconds to capture/intercept before returning results (default: 10)
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - requests: List of captured requests (when action is "log"), each with method, url, status, headers, resource_type
        - blocked: Number of requests blocked (when action is "block")
        - mocked: Number of requests mocked (when action is "mock")
        - error: Error message if failed
    """
    safe_pattern = url_pattern.replace("\\", "\\\\").replace("'", "\\'")

    if action == "block":
        route_code = f"""
        let blocked = 0;
        await page.route('{safe_pattern}', route => {{
            blocked++;
            route.abort();
        }});
        await page.waitForTimeout({duration * 1000});
        await page.unroute('{safe_pattern}');
        console.log(JSON.stringify({{ status: 'ok', action: 'block', blocked }}));
"""
    elif action == "mock":
        if mock_body is None:
            mock_body = "{}"
        encoded_body = base64.b64encode(mock_body.encode()).decode()
        route_code = f"""
        let mocked = 0;
        const body = Buffer.from('{encoded_body}', 'base64').toString('utf8');
        await page.route('{safe_pattern}', route => {{
            mocked++;
            route.fulfill({{
                status: {mock_status},
                contentType: '{mock_content_type}',
                body: body
            }});
        }});
        await page.waitForTimeout({duration * 1000});
        await page.unroute('{safe_pattern}');
        console.log(JSON.stringify({{ status: 'ok', action: 'mock', mocked }}));
"""
    else:
        # log
        route_code = f"""
        const captured = [];
        page.on('request', req => {{
            captured.push({{
                method: req.method(),
                url: req.url(),
                resource_type: req.resourceType(),
                headers: req.headers()
            }});
        }});
        page.on('response', resp => {{
            const entry = captured.find(r => r.url === resp.url());
            if (entry) {{
                entry.status = resp.status();
                entry.status_text = resp.statusText();
                entry.response_headers = resp.headers();
            }}
        }});
        await page.waitForTimeout({duration * 1000});
        // Filter to pattern if not **/*
        let results = captured;
        if ('{safe_pattern}' !== '**/*') {{
            const glob = '{safe_pattern}'.replace(/\\*/g, '.*');
            const re = new RegExp(glob);
            results = captured.filter(r => re.test(r.url));
        }}
        console.log(JSON.stringify({{
            status: 'ok',
            action: 'log',
            requests: results.slice(0, 200),
            total: results.length
        }}));
"""

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        {route_code}
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    subprocess_timeout = duration + 20
    return run_node(script, timeout=60, err_timeout="Intercept timed out")

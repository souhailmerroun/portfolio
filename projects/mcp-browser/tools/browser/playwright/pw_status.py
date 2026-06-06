"""
Check if Chrome is running with CDP and return connection info.

Uses Playwright's context.pages() for tab listing so indices match
all other pw_* tools (pw_click, pw_goto, pw_close_tab, etc.).
"""
import json
import os
import subprocess
import urllib.request

from tools.browser.config import REMOTE_CHROME_DIR


def pw_status(port: int = 9222) -> dict:
    """
    Check if Chrome is running with remote debugging and return status info.

    Args:
        port: The remote debugging port to check (default: 9222)

    Returns:
        A dictionary containing:
        - running: True if Chrome is responding on the given port
        - cdp_url: The CDP endpoint URL
        - browser: Browser version string
        - pages: List of open pages with index, title and url
        - error: Error message if not running
    """
    cdp_url = f"http://localhost:{port}"

    # Check browser version via CDP (lightweight, no Playwright needed)
    try:
        req = urllib.request.urlopen(f"{cdp_url}/json/version", timeout=3)
        version_data = json.loads(req.read())
        req.close()
    except Exception:
        return {
            "running": False,
            "cdp_url": cdp_url,
            "error": f"No Chrome responding on port {port}"
        }

    # Get open pages via Playwright so indices match other pw_* tools
    pages = []
    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        const ctxPages = context.pages();
        const tabs = [];
        for (let i = 0; i < ctxPages.length; i++) {{
            tabs.push({{
                index: i,
                title: await ctxPages[i].title(),
                url: ctxPages[i].url()
            }});
        }}
        console.log(JSON.stringify({{ status: 'ok', tabs: tabs }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    try:
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, timeout=15,
            cwd=os.path.abspath(REMOTE_CHROME_DIR)
        )
        output = result.stdout.strip()
        if output:
            for line in reversed(output.split('\n')):
                try:
                    data = json.loads(line)
                    if data.get("status") == "ok":
                        pages = data.get("tabs", [])
                    break
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return {
        "running": True,
        "cdp_url": cdp_url,
        "browser": version_data.get("Browser", "unknown"),
        "websocket_url": version_data.get("webSocketDebuggerUrl", ""),
        "pages": pages,
        "page_count": len(pages)
    }

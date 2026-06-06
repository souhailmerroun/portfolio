"""
Launch a new Playwright browser session connected to a running server via CDP.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR


def pw_launch(url: str = "http://localhost:9222") -> dict:
    """
    Launch a new Playwright browser session by connecting to a running Chrome/Chromium via CDP.

    Args:
        url: The CDP endpoint URL of the running browser (e.g., "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "connected" or "error"
        - url: The CDP endpoint used
        - pages: List of open pages with their titles and URLs
        - error: Error message if failed
    """
    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    try {{
        const browser = await chromium.connectOverCDP('{url}');
        const contexts = browser.contexts();
        const pages = [];

        for (const context of contexts) {{
            for (const page of context.pages()) {{
                pages.push({{
                    title: await page.title(),
                    url: page.url()
                }});
            }}
        }}

        console.log(JSON.stringify({{
            status: 'connected',
            url: '{url}',
            pages: pages,
            contexts: contexts.length
        }}));

        await browser.close();
    }} catch (e) {{
        console.log(JSON.stringify({{
            status: 'error',
            url: '{url}',
            error: e.message
        }}));
    }}
}})();
"""
    try:
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=os.path.abspath(REMOTE_CHROME_DIR)
        )

        output = result.stdout.strip()
        if output:
            return json.loads(output)

        return {
            "status": "error",
            "url": url,
            "error": result.stderr.strip() or "No output from Playwright"
        }

    except subprocess.TimeoutExpired:
        return {"status": "error", "url": url, "error": "Connection timed out"}
    except Exception as e:
        return {"status": "error", "url": url, "error": str(e)}

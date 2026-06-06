"""
Reload all unpacked/developer extensions in Arc browser.

Uses resolve_tab (to find the chrome://extensions page),
pw_evaluate (to click reload buttons), and open_arc_tab
(to open the extensions page if not already open).

Prerequisites:
    1. A chrome://extensions/ tab should be open in Arc.
    2. If not, the tool will open one automatically.
"""
import time

from tools.browser.arc.open_arc_tab import open_arc_tab
from tools.browser.arc.fetch_arc_tabs import fetch_arc_tabs
from tools.browser.playwright.pw_list_tabs import pw_list_tabs
from tools.browser.playwright.pw_wait import pw_wait
from tools.browser.playwright.pw_evaluate import pw_evaluate


def reload_arc_extensions(cdp_url: str = "http://localhost:9222") -> dict:
    """
    Reload all extensions that have a developer reload button in Arc browser.

    Args:
        cdp_url: The CDP endpoint URL (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - reloaded: List of extension names that were reloaded
        - total: Number of extensions reloaded
        - error: Error message if failed
    """
    # Find the chrome://extensions/ page via Playwright
    # (Arc shows arc://extensions/ but Playwright sees chrome://extensions/)
    def find_extensions_page():
        pw_result = pw_list_tabs(cdp_url=cdp_url)
        if pw_result.get("status") == "error":
            return None, pw_result
        for tab in pw_result.get("tabs", []):
            if tab.get("url") in ("chrome://extensions/", "arc://extensions/"):
                return tab["index"], None
        return None, None

    page_index, err = find_extensions_page()
    if err:
        return err

    # Open one if not found
    if page_index is None:
        open_result = open_arc_tab(url="chrome://extensions/")
        if open_result.get("status") == "error":
            return open_result
        time.sleep(2)

        page_index, err = find_extensions_page()
        if err:
            return err
        if page_index is None:
            return {"status": "error", "error": "Opened chrome://extensions/ but could not find it via Playwright."}

    # Wait for the page to be ready
    wait_result = pw_wait(page_index=page_index, timeout=2000, cdp_url=cdp_url)
    if wait_result.get("status") == "error":
        return wait_result

    # Click all developer reload buttons
    js = """(async () => {
        const mgr = document.querySelector('extensions-manager');
        if (!mgr) return JSON.stringify([]);
        const itemList = mgr.shadowRoot.querySelector('extensions-item-list');
        if (!itemList) return JSON.stringify([]);
        const items = itemList.shadowRoot.querySelectorAll('extensions-item');
        const reloaded = [];
        for (const item of items) {
            const btn = item.shadowRoot.querySelector('#dev-reload-button');
            if (btn) {
                btn.click();
                const name = item.shadowRoot.querySelector('#name')?.textContent?.trim();
                if (name) reloaded.push(name);
            }
        }
        return JSON.stringify(reloaded);
    })()"""

    eval_result = pw_evaluate(expression=js, page_index=page_index, cdp_url=cdp_url)
    if eval_result.get("status") == "error":
        return eval_result

    value = eval_result.get("result", "[]")
    try:
        reloaded = __import__("json").loads(value) if isinstance(value, str) else []
    except Exception:
        reloaded = []

    return {
        "status": "ok",
        "reloaded": reloaded,
        "total": len(reloaded)
    }

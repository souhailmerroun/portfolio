"""
Bridge between Arc tab IDs and Playwright page indices.

Fetches tabs from both Arc (AppleScript) and Playwright (CDP),
matches them by URL, and returns the full mapping.
"""

from tools.browser.arc.fetch_arc_tabs import fetch_arc_tabs
from tools.browser.playwright.pw_list_tabs import pw_list_tabs


def resolve_tab(tab_id: str = None, page_index: int = None, cdp_url: str = "http://localhost:9222") -> dict:
    """
    Resolve between Arc tab ID and Playwright page index.

    Pass one of tab_id or page_index to get the other.

    Args:
        tab_id: An Arc tab ID to resolve to a Playwright page index.
        page_index: A Playwright page index to resolve to an Arc tab ID.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - tab_id: The Arc tab ID
        - page_index: The Playwright page index
        - url: The tab URL
        - title: The tab title
        - error: Error message if failed
    """
    if tab_id is None and page_index is None:
        return {"status": "error", "error": "Provide either tab_id or page_index"}

    # Fetch both sides
    arc_result = fetch_arc_tabs()
    if arc_result.get("status") == "error":
        return {"status": "error", "error": f"Arc: {arc_result.get('error')}"}

    pw_result = pw_list_tabs(cdp_url=cdp_url)
    if pw_result.get("status") == "error":
        return {"status": "error", "error": f"Playwright: {pw_result.get('error')}"}

    arc_tabs = arc_result.get("tabs", [])
    pw_tabs = pw_result.get("tabs", [])

    if tab_id is not None:
        # Find the Arc tab by ID → get its URL → find matching Playwright page
        arc_tab = None
        for t in arc_tabs:
            if t["id"] == tab_id:
                arc_tab = t
                break

        if not arc_tab:
            return {"status": "error", "error": f"No Arc tab with ID: {tab_id}"}

        arc_url = arc_tab["url"]
        for pw_tab in pw_tabs:
            if pw_tab["url"] == arc_url:
                return {
                    "status": "ok",
                    "tab_id": tab_id,
                    "page_index": pw_tab["index"],
                    "url": arc_url,
                    "title": arc_tab["title"],
                }

        return {"status": "error", "error": f"Arc tab '{tab_id}' has URL '{arc_url}' but no matching Playwright page found"}

    else:
        # Find the Playwright page by index → get its URL → find matching Arc tab
        pw_tab = None
        for t in pw_tabs:
            if t["index"] == page_index:
                pw_tab = t
                break

        if not pw_tab:
            return {"status": "error", "error": f"No Playwright page at index: {page_index}"}

        pw_url = pw_tab["url"]
        for arc_tab in arc_tabs:
            if arc_tab["url"] == pw_url:
                return {
                    "status": "ok",
                    "tab_id": arc_tab["id"],
                    "page_index": page_index,
                    "url": pw_url,
                    "title": pw_tab["title"],
                }

        return {"status": "error", "error": f"Playwright page {page_index} has URL '{pw_url}' but no matching Arc tab found"}

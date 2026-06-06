"""
Fetch all open tabs from the Arc browser.
"""
import json
import subprocess
import urllib.request


def _cdp_fetch_tabs() -> dict:
    """Fetch tabs via CDP when AppleScript is unavailable (e.g. screen locked)."""
    try:
        with urllib.request.urlopen("http://localhost:9222/json", timeout=5) as r:
            cdp_tabs = json.loads(r.read())
        tabs = []
        for t in cdp_tabs:
            url = t.get("url", "")
            if url.startswith("chrome-extension://"):
                continue
            tabs.append({
                "title": t.get("title", ""),
                "url": url,
                "id": t.get("id", ""),
            })
        return {"status": "ok", "tabs": tabs, "total": len(tabs)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def fetch_arc_tabs() -> dict:
    """
    Fetch all open tabs from the Arc browser via AppleScript.
    Falls back to CDP (port 9222) when AppleScript times out (e.g. screen locked).

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - tabs: List of tabs with their title, url, and id
        - total: Total number of open tabs
        - error: Error message if failed
    """
    try:
        # Fetch tabs from every window (not just front) to catch Little Arc windows too
        def _every_window_script(prop):
            return f"""
tell application "Arc"
    set r to {{}}
    repeat with w in every window
        try
            set r to r & ({prop} of every tab of w)
        end try
    end repeat
    return r
end tell
"""

        titles_result = subprocess.run(
            ["osascript", "-e", _every_window_script("title")],
            capture_output=True, text=True, timeout=5
        )
        urls_result = subprocess.run(
            ["osascript", "-e", _every_window_script("URL")],
            capture_output=True, text=True, timeout=5
        )
        ids_result = subprocess.run(
            ["osascript", "-e", _every_window_script("id")],
            capture_output=True, text=True, timeout=5
        )

        if any(r.returncode != 0 for r in [titles_result, urls_result, ids_result]):
            return _cdp_fetch_tabs()

        titles = [t.strip() for t in titles_result.stdout.strip().split(", ")] if titles_result.stdout.strip() else []
        urls = [u.strip() for u in urls_result.stdout.strip().split(", ")] if urls_result.stdout.strip() else []
        ids = [i.strip() for i in ids_result.stdout.strip().split(", ")] if ids_result.stdout.strip() else []

        tabs = []
        for i in range(max(len(titles), len(urls), len(ids))):
            tabs.append({
                "title": titles[i] if i < len(titles) else "",
                "url": urls[i] if i < len(urls) else "",
                "id": ids[i] if i < len(ids) else ""
            })

        return {
            "status": "ok",
            "tabs": tabs,
            "total": len(tabs)
        }
    except subprocess.TimeoutExpired:
        return _cdp_fetch_tabs()
    except Exception as e:
        return {"status": "error", "error": str(e)}

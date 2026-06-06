"""
Close a tab in the Arc browser by its ID.
"""
import re
import subprocess
import urllib.request


def _is_cdp_id(tab_id: str) -> bool:
    """Return True if tab_id is a CDP target ID (hex string, 16+ chars)."""
    return bool(re.fullmatch(r"[0-9A-Fa-f]{16,}", tab_id.replace("-", "")))


def _cdp_close_tab(tab_id: str) -> dict:
    """Close a tab via CDP /json/close when AppleScript is unavailable."""
    try:
        with urllib.request.urlopen(
            f"http://localhost:9222/json/close/{tab_id}", timeout=5
        ) as r:
            r.read()
        return {"status": "ok", "tab_id": tab_id}
    except Exception as e:
        return {"status": "error", "error": str(e), "tab_id": tab_id}


def close_arc_tab(tab_id: str) -> dict:
    """
    Close a tab in the Arc browser by its ID.

    Args:
        tab_id: The ID of the tab to close (get IDs from fetch_arc_tabs).
            Accepts both AppleScript IDs and CDP target IDs.

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - tab_id: The ID of the closed tab
        - error: Error message if failed
    """
    if _is_cdp_id(tab_id):
        return _cdp_close_tab(tab_id)

    safe_id = tab_id.replace('"', '\\"')
    # Search every window (not just front) to also close tabs in Little Arc windows
    script = f"""
tell application "Arc"
    repeat with w in every window
        try
            close (every tab of w whose id is "{safe_id}")
        end try
    end repeat
end tell
"""

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return {"status": "ok", "tab_id": tab_id}
        return {"status": "error", "error": result.stderr.strip(), "tab_id": tab_id}
    except subprocess.TimeoutExpired:
        return _cdp_close_tab(tab_id)
    except Exception as e:
        return {"status": "error", "error": str(e)}

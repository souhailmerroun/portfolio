"""
Navigate the active tab in Arc browser to a new URL.
"""
import subprocess


def navigate_arc_tab(url: str) -> dict:
    """
    Navigate the active tab in Arc browser to a new URL.

    Args:
        url: The URL to navigate to

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - url: The URL navigated to
        - error: Error message if failed
    """
    safe_url = url.replace('"', '\\"')
    script = f'tell application "Arc" to set URL of active tab of front window to "{safe_url}"'

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return {"status": "ok", "url": url}
        return {"status": "error", "error": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

"""
Fetch the current active tab from the Arc browser.
"""
import subprocess
import json


def fetch_arc_current_tab() -> dict:
    """
    Fetch the current active tab from the Arc browser via AppleScript.

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - title: The title of the active tab
        - url: The URL of the active tab
        - space: The name of the active space
        - error: Error message if failed
    """
    script = """
tell application "Arc"
    set tabTitle to title of active tab of front window
    set tabURL to URL of active tab of front window
    set spaceName to title of active space of front window
    return "{\\"title\\": \\"" & tabTitle & "\\", \\"url\\": \\"" & tabURL & "\\", \\"space\\": \\"" & spaceName & "\\"}"
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        if output:
            data = json.loads(output)
            return {
                "status": "ok",
                "title": data["title"],
                "url": data["url"],
                "space": data["space"]
            }
        return {"status": "error", "error": result.stderr.strip() or "No output"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"JSON parse error: {str(e)}", "raw": output}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

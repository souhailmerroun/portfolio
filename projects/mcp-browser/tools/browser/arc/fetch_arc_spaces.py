"""
Fetch all spaces (profiles) from the Arc browser.
"""
import subprocess
import json


def fetch_arc_spaces() -> dict:
    """
    Fetch all spaces (profiles) from the Arc browser via AppleScript.

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - spaces: List of spaces with their name and id
        - active_space: The currently active space name
        - total: Total number of spaces
        - error: Error message if failed
    """
    script = """
tell application "Arc"
    set output to "{"
    set output to output & "\\"active_space\\": \\"" & (title of active space of front window) & "\\","
    set output to output & "\\"spaces\\": ["
    set spaceList to every space of front window
    set spaceCount to count of spaceList
    repeat with i from 1 to spaceCount
        set s to item i of spaceList
        set spaceTitle to title of s
        set spaceId to id of s
        set output to output & "{\\"name\\": \\"" & spaceTitle & "\\", \\"id\\": \\"" & spaceId & "\\"}"
        if i < spaceCount then
            set output to output & ","
        end if
    end repeat
    set output to output & "]}"
    return output
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
                "spaces": data["spaces"],
                "active_space": data["active_space"],
                "total": len(data["spaces"])
            }
        return {"status": "error", "error": result.stderr.strip() or "No output"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"JSON parse error: {str(e)}", "raw": output}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

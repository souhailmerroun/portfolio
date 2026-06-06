"""
Open a new tab in Arc browser, optionally in a specific space (profile).
"""
import fcntl
import hashlib
import os
import subprocess
import tempfile
import time
import urllib.request
from contextlib import contextmanager
from urllib.parse import urlparse

ARC_CDP_APP = os.environ.get(
    "MCP_ARC_CDP_APP",
    os.path.expanduser("~/Applications/Arc CDP.app"),
)
ARC_CDP_URL = "http://localhost:9222/json/version"


@contextmanager
def _host_lock(url: str):
    """Per-host file lock to prevent concurrent openers racing on the same site."""
    host = urlparse(url).netloc or "default"
    digest = hashlib.sha1(host.encode()).hexdigest()[:12]
    lock_path = os.path.join(tempfile.gettempdir(), f"arc_open_{digest}.lock")
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def _cdp_ready() -> bool:
    try:
        with urllib.request.urlopen(ARC_CDP_URL, timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _ensure_arc_with_cdp():
    """Ensure Arc is running with CDP enabled. Uses Arc CDP.app to launch if needed."""
    if _cdp_ready():
        return
    # Arc is not running with CDP — start it via the CDP launcher app
    subprocess.run(["open", "-a", ARC_CDP_APP], capture_output=True, timeout=10)
    for _ in range(20):
        if _cdp_ready():
            return
        time.sleep(1)


def _open_via_open_command(url: str) -> dict:
    """Fallback: open URL in Arc via the macOS 'open' command (works when screen is locked)."""
    try:
        _ensure_arc_with_cdp()
        result = subprocess.run(
            ["open", "-a", "Arc", url],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return {"status": "ok", "url": url, "space": "default"}
        return {"status": "error", "error": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def open_arc_tab(url: str, space: str = None) -> dict:
    """
    Open a new tab in Arc browser, optionally in a specific space (profile).

    Args:
        url: The URL to open in the new tab
        space: The name of the space/profile to open the tab in (optional, uses active space if omitted)

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - url: The URL that was opened
        - space: The space the tab was opened in
        - error: Error message if failed
    """
    safe_url = url.replace('"', '\\"')

    # Ensure Arc is running with CDP. Use the Arc CDP.app so CDP stays enabled.
    # Avoid AppleScript 'count of windows' which hangs when the screen is locked.
    _ensure_arc_with_cdp()

    if space:
        safe_space = space.replace('"', '\\"')
        tab_script = f"""
tell application "Arc"
    tell front window
        tell space "{safe_space}"
            make new tab with properties {{URL:"{safe_url}"}}
        end tell
    end tell
end tell
"""
    else:
        tab_script = f"""
tell application "Arc"
    tell front window
        make new tab with properties {{URL:"{safe_url}"}}
    end tell
end tell
"""

    try:
        # Save frontmost app so we can restore focus after Arc steals it
        try:
            prev_app = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
                capture_output=True, text=True, timeout=3
            ).stdout.strip()
        except Exception:
            prev_app = ""

        with _host_lock(url):
            result = subprocess.run(
                ["osascript", "-e", tab_script],
                capture_output=True, text=True, timeout=8
            )

        # Restore focus to previous app
        if prev_app and prev_app != "Arc":
            try:
                subprocess.run(
                    ["osascript", "-e", f'tell application "{prev_app}" to activate'],
                    capture_output=True, text=True, timeout=3
                )
            except Exception:
                pass

        if result.returncode == 0:
            return {
                "status": "ok",
                "url": url,
                "space": space or "active"
            }
        # AppleScript failed (e.g. no front window when screen locked) — fall back to 'open'
        return _open_via_open_command(url)
    except subprocess.TimeoutExpired:
        # AppleScript hung (screen locked) — fall back to 'open' command
        return _open_via_open_command(url)
    except Exception as e:
        return {"status": "error", "error": str(e)}

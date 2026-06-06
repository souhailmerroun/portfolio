"""
Atomically find-or-open a tab in Arc for a given URL fragment.

Prevents races between parallel scripts that each do:
    tab_id = find_by_fragment(...)
    if tab_id is None: open_arc_tab(...)

Because the check-and-open is not atomic, two concurrent callers can both
miss the existing tab and each open a new one, leaving duplicates.
ensure_arc_tab serializes the operation per URL fragment via a file lock.
"""
import fcntl
import hashlib
import os
import tempfile
import time
from contextlib import contextmanager

from tools.browser.arc.fetch_arc_tabs import fetch_arc_tabs
from tools.browser.arc.open_arc_tab import open_arc_tab


@contextmanager
def _fragment_lock(fragment: str):
    digest = hashlib.sha1(fragment.encode()).hexdigest()[:12]
    lock_path = os.path.join(tempfile.gettempdir(), f"arc_ensure_{digest}.lock")
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def _find_tab_id(url_fragment: str):
    tabs = fetch_arc_tabs()
    if tabs.get("status") != "ok":
        return None
    for tab in tabs.get("tabs", []):
        if url_fragment in tab.get("url", ""):
            return tab.get("id")
    return None


def ensure_arc_tab(
    url_fragment: str,
    url: str,
    space: str = None,
    open_wait_seconds: float = 8.0,
) -> dict:
    """
    Return an Arc tab id whose URL contains url_fragment, opening a new tab if needed.

    The entire find-or-open operation runs under a per-fragment file lock, so
    concurrent callers targeting the same site cannot both open a tab.

    Args:
        url_fragment: Substring to match against existing tab URLs.
        url: URL to open if no matching tab is found.
        space: Arc space/profile to open the tab in (optional).
        open_wait_seconds: How long to wait after opening before re-finding the tab.

    Returns:
        {
          "status": "ok" | "error",
          "tab_id": <str>,
          "opened_new": <bool>,
          "error": <str, only on error>
        }
    """
    with _fragment_lock(url_fragment):
        tab_id = _find_tab_id(url_fragment)
        if tab_id is not None:
            return {"status": "ok", "tab_id": tab_id, "opened_new": False}

        open_result = open_arc_tab(url, space=space)
        if open_result.get("status") != "ok":
            return {"status": "error", "error": f"Failed to open tab: {open_result.get('error')}"}

        time.sleep(open_wait_seconds)
        tab_id = _find_tab_id(url_fragment)
        if tab_id is None:
            return {"status": "error", "error": f"Could not find tab matching {url_fragment!r} after opening"}
        return {"status": "ok", "tab_id": tab_id, "opened_new": True}

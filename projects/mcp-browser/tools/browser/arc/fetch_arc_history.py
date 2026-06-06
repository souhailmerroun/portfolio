"""
Fetch browsing history for an Arc browser space.
"""
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta


# Chromium epoch offset: microseconds between 1601-01-01 and 1970-01-01
_CHROME_EPOCH_OFFSET = 11644473600000000


def _get_profile_map() -> dict:
    """Return a mapping of space name (lowercase) -> profile directory path."""
    local_state_path = os.path.expanduser(
        "~/Library/Application Support/Arc/User Data/Local State"
    )
    with open(local_state_path) as f:
        data = json.load(f)

    profiles = data.get("profile", {}).get("info_cache", {})
    base = os.path.expanduser("~/Library/Application Support/Arc/User Data")
    mapping = {}
    for dir_name, info in profiles.items():
        name = info.get("name", "")
        if name and name != "__ARC_SYSTEM_PROFILE":
            mapping[name.lower()] = os.path.join(base, dir_name)
    return mapping


def _chrome_time(dt: datetime) -> int:
    """Convert a datetime to Chromium microsecond timestamp."""
    unix_us = int(dt.timestamp() * 1_000_000)
    return unix_us + _CHROME_EPOCH_OFFSET


def _from_chrome_time(chrome_us: int) -> str:
    """Convert Chromium microsecond timestamp to local time ISO string."""
    unix_us = chrome_us - _CHROME_EPOCH_OFFSET
    dt = datetime.fromtimestamp(unix_us / 1_000_000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def fetch_arc_history(
    space: str = None,
    query: str = None,
    domain: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    Fetch browsing history for an Arc browser space.

    Args:
        space: Space name to fetch history for. If omitted, fetches from all spaces.
            Available spaces: "Personal", "Entrepreneur", "Digital Communication",
            "Well-being", "Lifestyle", "Planning", "Money", "Entertainment Noise",
            "18", "automation", "Dating", "Friend", "Entertainment", "Employee", "Musician".
        query: Search filter on URL or title (case-insensitive substring match).
        domain: Filter by domain (e.g. "github.com").
        start_date: Start date in "YYYY-MM-DD" format (inclusive). Defaults to 7 days ago.
            Example: "2026-03-18" fetches history from March 18th onward.
        end_date: End date in "YYYY-MM-DD" format (inclusive). Defaults to today.
            Example: "2026-03-18" fetches history up to end of March 18th.
        limit: Maximum number of results to return (default: 100).
        offset: Number of results to skip for pagination (default: 0).

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - history: List of history entries with url, title, visit_time, visit_count, and space
        - total: Total number of results (before pagination)
        - offset: Current offset
        - limit: Current limit
        - error: Error message if failed
    """
    try:
        profile_map = _get_profile_map()

        if space:
            match = profile_map.get(space.lower())
            if not match:
                available = sorted(set(
                    name.title() for name in profile_map.keys()
                ))
                return {
                    "status": "error",
                    "error": f"Space '{space}' not found. Available: {', '.join(available)}",
                }
            profiles_to_query = {space: match}
        else:
            profiles_to_query = {
                name.title(): path for name, path in profile_map.items()
            }

        now = datetime.now()
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = now - timedelta(days=7)
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            end_dt = now

        cutoff_start = _chrome_time(start_dt)
        cutoff_end = _chrome_time(end_dt)

        all_entries = []

        for space_name, profile_path in profiles_to_query.items():
            history_db = os.path.join(profile_path, "History")
            if not os.path.exists(history_db):
                continue

            # Copy DB to avoid lock issues with Arc
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            tmp.close()
            shutil.copy2(history_db, tmp.name)

            try:
                conn = sqlite3.connect(tmp.name)
                conn.row_factory = sqlite3.Row

                sql = """
                    SELECT u.url, u.title, u.visit_count, u.last_visit_time
                    FROM urls u
                    WHERE u.last_visit_time >= ? AND u.last_visit_time <= ?
                """
                params = [cutoff_start, cutoff_end]

                if query:
                    sql += " AND (u.url LIKE ? OR u.title LIKE ?)"
                    q = f"%{query}%"
                    params.extend([q, q])

                if domain:
                    sql += " AND u.url LIKE ?"
                    params.append(f"%://{domain}%")

                sql += " ORDER BY u.last_visit_time DESC LIMIT ? OFFSET ?"

                if len(profiles_to_query) == 1:
                    params.extend([limit, offset])
                else:
                    # Need enough rows from each space to cover pagination after merging
                    params.extend([limit + offset, 0])

                rows = conn.execute(sql, params).fetchall()
                conn.close()

                for row in rows:
                    all_entries.append({
                        "url": row["url"],
                        "title": row["title"],
                        "visit_count": row["visit_count"],
                        "visit_time": _from_chrome_time(row["last_visit_time"]),
                        "space": space_name,
                    })
            finally:
                os.unlink(tmp.name)

        # Sort all entries by visit time descending and apply pagination
        all_entries.sort(key=lambda e: e["visit_time"], reverse=True)
        total = len(all_entries)
        all_entries = all_entries[offset:offset + limit]

        import math
        total_pages = math.ceil(total / limit) if limit else 1
        current_page = (offset // limit) + 1 if limit else 1

        return {
            "status": "ok",
            "history": all_entries,
            "total": total,
            "offset": offset,
            "limit": limit,
            "current_page": current_page,
            "total_pages": total_pages,
            "has_more": offset + limit < total,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

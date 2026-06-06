"""Persistent-CDP execution helper for the pw_* browser tools.

Legacy model: every pw_* tool ran `subprocess.run(["node", "-e", script])` where
`script` did `chromium.connectOverCDP(...)` ... action ... `browser.close()`. That
paid a fresh Node process spawn + CDP handshake + full tab enumeration on EVERY
call.

`run_node(script, ...)` keeps the exact same per-call JS but routes it through a
long-lived Node daemon (`cdp_daemon.js`) that holds one connectOverCDP session and
reuses it. The action body is extracted from `script` and sent to the daemon. If
the daemon is unavailable, or returns nothing parseable, we fall back to the
original inline `node -e` path — so behaviour never regresses, it only gets faster
when the daemon is healthy.
"""
import json
import os
import subprocess
import threading
import time
import urllib.request

from tools.browser.config import REMOTE_CHROME_DIR

_RUNTIME = os.path.abspath(REMOTE_CHROME_DIR)
_DAEMON_JS = os.path.join(os.path.dirname(__file__), "cdp_daemon.js")
_HOST = "127.0.0.1"
_PORT = int(os.environ.get("MCP_CDP_DAEMON_PORT", "9224"))


def _url(path):
    return f"http://{_HOST}:{_PORT}{path}"


def _daemon_alive():
    try:
        with urllib.request.urlopen(_url("/health"), timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _ensure_daemon():
    if _daemon_alive():
        return True
    try:
        subprocess.Popen(
            ["node", _DAEMON_JS],
            cwd=_RUNTIME,
            env={
                **os.environ,
                "MCP_CDP_DAEMON_PORT": str(_PORT),
                "MCP_CDP_RUNTIME": _RUNTIME,
                "NODE_PATH": os.path.join(_RUNTIME, "node_modules"),
            },
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        return False
    for _ in range(50):  # up to ~5s for first-time startup
        if _daemon_alive():
            return True
        time.sleep(0.1)
    return False


def _parse_lines(lines):
    """Return the last line that parses as JSON, mirroring the legacy parser."""
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def _extract_body(script):
    """Pull the per-call action body + cdp_url out of a legacy full script.

    The body is everything between the connectOverCDP line and the IIFE's
    `} catch` — i.e. it begins with `const context = browser.contexts()[0];`,
    uses browser/console/chromium/require and console.log/return, exactly the
    scope the daemon provides. Returns (body, cdp_url) or (None, None) when the
    script doesn't fit the expected shape (then the caller uses the fallback).
    """
    if "connectOverCDP" not in script:
        return None, None
    i = script.find("connectOverCDP")
    lp = script.find("(", i)
    rp = script.find(")", lp)
    if lp == -1 or rp == -1:
        return None, None
    raw = script[lp + 1:rp].strip()
    try:
        cdp_url = json.loads(raw)          # json.dumps(cdp_url) form
    except Exception:
        cdp_url = raw.strip("'\"") or "http://localhost:9222"
    nl = script.find("\n", i)
    cat = script.find("} catch", nl)
    if nl == -1 or cat == -1:
        return None, None
    body = script[nl + 1:cat]
    if not body.strip() or "connectOverCDP" in body:
        return None, None
    return body, cdp_url


def _run_subprocess(script, timeout, err_timeout):
    """The original inline `node -e` path — used as a fallback."""
    try:
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, timeout=timeout,
            cwd=_RUNTIME,
        )
        out = result.stdout.strip()
        parsed = _parse_lines(out.split("\n")) if out else None
        if parsed is not None:
            return parsed
        return {"status": "error", "error": result.stderr.strip() or "No output"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": err_timeout}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_node(script, timeout=30, err_timeout="timed out"):
    """Execute a legacy pw_* `node -e` script via the persistent daemon.

    Falls back to the inline subprocess path if the daemon can't be used or
    doesn't return a parseable result.
    """
    body, cdp_url = _extract_body(script)
    if body is not None and _ensure_daemon():
        try:
            payload = json.dumps({
                "cdp_url": cdp_url,
                "body": body,
                "timeout_ms": int(timeout * 1000),
            }).encode()
            req = urllib.request.Request(
                _url("/run"), data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout + 5) as r:
                resp = json.loads(r.read().decode())
            if resp.get("ok"):
                parsed = _parse_lines(resp.get("lines", []))
                if parsed is not None:
                    return parsed
            # ok but nothing parseable → fall through to the subprocess path
        except Exception:
            pass  # daemon trouble → fall through
    return _run_subprocess(script, timeout, err_timeout)


def _prewarm():
    """Best-effort: bring the daemon (and its CDP connection) up at import time
    so the very first tool call doesn't pay the node spawn + connectOverCDP. All
    failures (e.g. browser not running) are swallowed — the lazy path still works.
    """
    try:
        if not _ensure_daemon():
            return
        body = ("const c = browser.contexts(); "
                "console.log(JSON.stringify({ status: 'ok' }));")
        payload = json.dumps({
            "cdp_url": "http://localhost:9222",
            "body": body,
            "timeout_ms": 8000,
        }).encode()
        req = urllib.request.Request(
            _url("/run"), data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception:
        pass


# Kick the warm-up off once, in the background, when this module is first
# imported (i.e. when the MCP server loads the browser tools).
threading.Thread(target=_prewarm, daemon=True).start()

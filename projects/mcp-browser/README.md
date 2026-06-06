# mcp-browser

A production-grade [FastMCP](https://github.com/jlowin/fastmcp) server that exposes **Playwright browser automation** as MCP tools — letting Claude (or any MCP client) drive a real browser tab-by-tab without ever touching the user's active session.

Built and used daily as part of an autonomous agentic fleet that fills forms, navigates sites, applies to jobs, and manages profiles — all via Claude tool calls.

---

## What's inside

### 30+ `pw_*` browser primitives

Every tool follows the same contract: target a specific tab (`page_index` or `page_url`), never tab 0 (the user's active tab). Returns structured JSON — no raw HTML noise.

| Tool | What it does |
|---|---|
| `pw_goto` | Navigate to a URL |
| `pw_click` | Click a CSS selector |
| `pw_fill` | Fill a form field (instant set) |
| `pw_type` | Type text key-by-key (with delay) |
| `pw_press` | Send a keyboard key |
| `pw_snapshot` | Get a compact map of clickable/fillable elements — the token-efficient alternative to dumping the full DOM |
| `pw_get_text` | Read visible text content |
| `pw_get_html` | Read the raw HTML (with optional region scoping) |
| `pw_screenshot` | Capture the page as a base64 PNG |
| `pw_scroll` | Scroll to top/bottom/by pixels |
| `pw_select` | Choose a `<select>` option |
| `pw_hover` | Hover a selector |
| `pw_evaluate` | Run arbitrary JS in the page and return the value |
| `pw_wait` | Sleep N ms |
| `pw_wait_for` | Wait for a CSS selector to appear |
| `pw_new_tab` | Open a new background tab |
| `pw_close_tab` | Close a tab by index |
| `pw_list_tabs` | List all open tabs |
| `pw_back` / `pw_forward` / `pw_reload` | Browser history navigation |
| `pw_download` / `pw_save_download` | Trigger and save file downloads |
| `pw_handle_filechooser` | Intercept file picker dialogs |
| `pw_intercept` | Intercept / block network requests |
| `pw_pdf` | Export page to PDF |
| `pw_status` | Get tab URL + title |
| `pw_cookies` | Read cookies |
| `pw_console` | Capture browser console output |
| `pw_test` | Assert a condition, return pass/fail |
| `pw_act` | **Run a whole step-list in ONE round-trip** (goto → fill → click → snapshot) — the biggest speedup available |

### Arc browser tab management

Tools for inspecting and driving [Arc](https://arc.net/) tabs by space/title/URL — works alongside the `pw_*` primitives.

### Compiled recipes

A `pw_recipe` dispatcher that runs pre-verified multi-step flows without burning schema tokens. Two examples included:

- `the_internet/login` — canonical UI-automation sandbox (deterministic creds, read-only)
- `wikipedia/summary` — fetch an article summary

---

## Architecture

```
server.py                 ← 3-line FastMCP entry point
server_base.py            ← factory: auto-discovers tools + starts file watcher
tools_registry.py         ← walks tools/ and registers every non-private function

tools/
  browser/
    config.py             ← MCP_PLAYWRIGHT_RUNTIME env var (path to Node runtime)
    recipe.py             ← pw_recipe dispatcher
    playwright/
      _cdp.py             ← persistent CDP daemon bridge (one connectOverCDP per session)
      _resolve_page.py    ← shared JS: resolve page by index or URL substring
      cdp_daemon.js       ← long-lived Node daemon; reuses the CDP connection across calls
      pw_*.py             ← one file per tool; auto-registered at startup
    arc/
      *.py                ← Arc-specific tab management tools
  recipes/
    the_internet/login.py
    wikipedia/summary.py
playwright-runtime/
  package.json            ← { "dependencies": { "playwright": "^1.58.2" } }
```

### The CDP daemon

By default every Playwright tool would spawn a fresh `node -e` process, pay a full `connectOverCDP` handshake, and enumerate all tabs — adding ~300–800 ms per call. The daemon (`cdp_daemon.js`) holds **one live CDP connection** and routes action bodies to it over HTTP on `localhost:9224`. Result: per-call overhead drops to near zero; the first call pays the startup cost, every subsequent one is just the action.

The daemon is started lazily on the first tool call and exits after 10 minutes idle.

### Auto-discovery

`tools_registry.py` walks `tools/` at startup and registers every non-underscore `.py` file as an MCP tool — no explicit imports, no decorator boilerplate. Add a new tool file → it's live on the next hot-reload (via `mcp-hmr`).

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Chromium-family browser running with `--remote-debugging-port=9222`
  (Arc on macOS does this automatically; for others: `chromium --remote-debugging-port=9222`)

### Install

```bash
# Python deps
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Node Playwright runtime
cd playwright-runtime && npm install && cd ..
```

### Register with Claude

Add to your `claude_desktop_config.json` (or equivalent MCP config):

```json
{
  "mcpServers": {
    "mcp-browser": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "server"],
      "cwd": "/path/to/mcp-browser",
      "env": {
        "MCP_PLAYWRIGHT_RUNTIME": "/path/to/mcp-browser/playwright-runtime"
      }
    }
  }
}
```

### Run standalone

```bash
python server.py
```

---

## Usage pattern

A typical Claude interaction:

```
# 1. Open a new worker tab (never hijack tab 0 — that's the user's view)
pw_new_tab() → { page_index: 3 }

# 2. Navigate
pw_goto(url="https://example.com/login", page_index=3)

# 3. Inspect what's actionable
pw_snapshot(page_index=3)  → { elements: [ { tag: "input", label: "Email", selector: "#email" }, ... ] }

# 4. Fill and submit
pw_fill(selector="#email", value="me@example.com", page_index=3)
pw_fill(selector="#password", value="...", page_index=3)
pw_click(selector="button[type='submit']", page_index=3)

# 5. Verify
pw_get_text(selector=".dashboard-header", page_index=3)
```

Or run the whole flow in one call with `pw_act`:

```python
pw_act(steps=[
    {"goto": "https://example.com/login"},
    {"fill": "#email", "value": "me@example.com"},
    {"fill": "#password", "value": "..."},
    {"click": "button[type='submit']"},
    {"wait_for": ".dashboard-header"},
    {"text": ".dashboard-header"},
], new_tab=True)
```

---

## Design decisions

**Tab 0 is sacred.** Every tool refuses to default to tab 0. The user's active tab must never be hijacked mid-session — this is a hard invariant, not a convention.

**One tool = one file.** Each `pw_*.py` is a standalone module with a single exported function. Auto-discovery means adding a tool is as simple as dropping a new file.

**JSON in, JSON out.** Every tool returns `{ status: "ok"|"error", ... }`. No exceptions surface as unhandled Python tracebacks.

**`pw_act` for multi-step flows.** N round-trips of `goto → fill → click → snapshot` cost N × (model latency + daemon call). `pw_act` collapses them into 1 — especially valuable in agentic loops.

---

## License

MIT

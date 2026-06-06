"""
Compact interactive-element map of the page — the cheap way to "see" what you can
act on, without dumping the whole DOM.

This is the token-efficient substitute for pw_get_html when the goal is NAVIGATION
(what can I click / fill / select?). It returns only the actionable elements —
links, buttons, inputs, selects, and ARIA widgets — each with a visible label and a
best-effort CSS selector you can hand straight to pw_click / pw_fill / pw_select.

Typical cost: ~1–2k tokens vs ~10–50k for raw pw_get_html on a modern app.

Order of preference for reading a page:
  1. pw_snapshot         → navigate (what's actionable + its selector)   ← cheapest
  2. pw_get_text         → read the visible content
  3. pw_get_html(clean)  → need the actual structure/markup of a region
  4. pw_screenshot       → only for visual-only / canvas / custom-widget UIs
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node


def pw_snapshot(selector: str = None, limit: int = 200, include_hidden: bool = False, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Get a compact map of the page's interactive (clickable / fillable) elements.

    Args:
        selector: limit the scan to a region (CSS selector); omit to scan the whole page.
        limit: max elements to return (default 200; oldest-in-DOM first).
        include_hidden: include non-visible elements too (default false = visible only).
        page_index: Which tab — REQUIRED unless page_url is given; no default (tab 0 is the user's tab). From pw_list_tabs.
        cdp_url: CDP endpoint URL (default "http://localhost:9222").

    Returns:
        - status: "ok" or "error"
        - url, title: the page's URL + title
        - count: number of elements returned
        - elements: list of { tag, type, label, selector, name } — `selector` is a
          best-effort CSS handle (#id, [data-testid], tag[name=…], tag[aria-label=…])
          to use with pw_click / pw_fill; empty if none could be derived (use label/text).
        - error: error message if failed
    """
    sel_js = json.dumps(selector)
    limit_js = str(int(limit))
    inc_js = "true" if include_hidden else "false"
    resolve = resolve_page_js(page_index, page_url)

    snap = (
        "const data = await page.evaluate(({ rootSel, limit, includeHidden }) => {\n"
        "  const root = rootSel ? document.querySelector(rootSel) : document;\n"
        "  if (!root) return null;\n"
        "  const SEL = 'a,button,input,textarea,select,summary,[role=button],[role=link],[role=tab],[role=menuitem],[role=checkbox],[role=switch],[role=radio],[role=combobox],[contenteditable=\\\"\\\"],[contenteditable=true],[onclick]';\n"
        "  const esc = (s) => (window.CSS && CSS.escape) ? CSS.escape(s) : String(s).replace(/[^a-zA-Z0-9_-]/g, '\\\\$&');\n"
        "  const out = []; const seen = new Set();\n"
        "  for (const el of root.querySelectorAll(SEL)) {\n"
        "    const tag = el.tagName.toLowerCase();\n"
        "    const visible = el.offsetParent !== null || tag === 'input' || el.getClientRects().length > 0;\n"
        "    if (!includeHidden && !visible) continue;\n"
        "    const tid = el.getAttribute('data-testid');\n"
        "    const nm = el.getAttribute('name');\n"
        "    const al = el.getAttribute('aria-label');\n"
        "    let selector = '';\n"
        "    if (el.id) selector = '#' + esc(el.id);\n"
        "    else if (tid) selector = `[data-testid=\\\"${tid}\\\"]`;\n"
        "    else if (nm) selector = `${tag}[name=\\\"${nm}\\\"]`;\n"
        "    else if (al) selector = `${tag}[aria-label=\\\"${al}\\\"]`;\n"
        "    const label = (al || el.value || el.placeholder || (el.innerText || el.textContent || '') || el.getAttribute('title') || el.getAttribute('alt') || '').trim().replace(/\\s+/g, ' ').slice(0, 80);\n"
        "    if (!selector && !label) continue;\n"
        "    const key = tag + '|' + selector + '|' + label;\n"
        "    if (seen.has(key)) continue; seen.add(key);\n"
        "    const item = { tag, type: el.type || el.getAttribute('role') || '', label, selector };\n"
        "    if (nm) item.name = nm;\n"
        "    out.push(item);\n"
        "    if (out.length >= limit) break;\n"
        "  }\n"
        "  return { url: location.href, title: document.title, count: out.length, elements: out };\n"
        "}, { rootSel: " + sel_js + ", limit: " + limit_js + ", includeHidden: " + inc_js + " });"
    )

    script = (
        "const { chromium } = require('playwright');\n"
        "(async () => {\n"
        "  let browser;\n"
        "  try {\n"
        "    browser = await chromium.connectOverCDP(" + json.dumps(cdp_url) + ");\n"
        "    const context = browser.contexts()[0];\n"
        + resolve + "\n"
        + "    " + snap + "\n"
        "    if (data === null) { console.log(JSON.stringify({ status: 'error', error: 'root selector not found: ' + " + sel_js + " })); return; }\n"
        "    console.log(JSON.stringify(Object.assign({ status: 'ok' }, data)));\n"
        "  } catch (e) {\n"
        "    console.log(JSON.stringify({ status: 'error', error: e.message }));\n"
        "  } finally {\n"
        "    if (browser) await browser.close();\n"
        "  }\n"
        "})();\n"
    )

    return run_node(script, timeout=30, err_timeout="Snapshot timed out")

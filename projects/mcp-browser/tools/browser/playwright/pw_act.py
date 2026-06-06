"""Run a whole sequence of browser actions in ONE call.

Every other pw_* tool is a single action = one model round-trip. A flow like
goto -> snapshot -> click -> snapshot is 4 round-trips (seconds each) wrapping
~5ms of actual work apiece. pw_act runs the entire step list server-side in a
single daemon call and returns the combined result, collapsing those N
round-trips into 1 — the biggest available speedup now that per-call latency is
already negligible.

Each step is a one-key dict naming the operation:

    {"goto": "https://x.com", "wait_until": "domcontentloaded"}
    {"click": "button.submit"}
    {"fill": "#email", "value": "me@x.com"}
    {"type": "#q", "text": "hello"}
    {"press": "Enter"}                      # or {"press":"Enter","selector":"#q"}
    {"wait": 500}                            # ms
    {"wait_for": ".results"}                 # wait for selector
    {"scroll": "bottom"}                     # "bottom" | "top" | <pixels>
    {"hover": ".menu"}
    {"select": "#country", "value": "FR"}
    {"text": ".article"}                     # innerText of a selector (or true = whole page)
    {"snapshot": true}                       # compact clickable/fillable map (or a selector)
    {"eval": "document.querySelector('x').click()"}   # run JS in the page; value returned

Targeting works like the other tools: pass page_index or page_url, or
new_tab=true to run the flow in a fresh worker tab (never tab 0).
"""
import json

from tools.browser.playwright._cdp import run_node
from tools.browser.playwright._resolve_page import resolve_page_js


def pw_act(steps, page_index: int = None, page_url: str = None,
           new_tab: bool = False, cdp_url: str = "http://localhost:9222") -> dict:
    """Execute a list of browser steps in a single round-trip.

    Args:
        steps: list of one-key dicts (see module docstring) run in order.
        page_index: target tab by index (from pw_list_tabs). No default.
        page_url: target tab whose URL contains this substring (preferred).
        new_tab: open a fresh tab and run the flow there (ignores page_index/url).
        cdp_url: CDP endpoint (default http://localhost:9222).

    Returns:
        { status, url, title, page_index, results: [ {op, ...} per step ] }
        On a step error: status="error", error set, results holds the steps
        that completed before the failure.
    """
    if not isinstance(steps, list) or not steps:
        return {"status": "error", "error": "steps must be a non-empty list of one-key dicts"}

    steps_js = json.dumps(steps)

    if new_tab:
        # Open the worker tab in the BACKGROUND so it never steals the user's
        # foreground view in Arc. context.newPage() activates the new tab (Arc
        # jumps to it); Target.createTarget({background:true}) does not.
        page_setup = (
            "        let page;\n"
            "        const __existing = context.pages()[0];\n"
            "        if (__existing) {\n"
            "          const __cdp = await context.newCDPSession(__existing);\n"
            "          const __before = new Set(context.pages());\n"
            "          await __cdp.send('Target.createTarget', { url: 'about:blank', background: true });\n"
            "          for (let i = 0; i < 80; i++) { page = context.pages().find(p => !__before.has(p)); if (page) break; await new Promise(r => setTimeout(r, 25)); }\n"
            "        }\n"
            "        if (!page) page = await context.newPage();\n"
            "        const pageIndex = context.pages().indexOf(page);\n"
        )
    else:
        page_setup = (
            "        " + resolve_page_js(page_index, page_url).strip() + "\n"
            "        const pageIndex = context.pages().indexOf(page);\n"
        )

    script = (
        "const { chromium } = require('playwright');\n"
        "(async () => {\n"
        "  let browser;\n"
        "  try {\n"
        "    browser = await chromium.connectOverCDP(" + json.dumps(cdp_url) + ");\n"
        "    const context = browser.contexts()[0];\n"
        + page_setup +
        "    const steps = " + steps_js + ";\n"
        "    const results = [];\n"
        "    async function __snap(sel, limit) {\n"
        "      return await page.evaluate((a) => {\n"
        "        const root = a.rootSel ? document.querySelector(a.rootSel) : document;\n"
        "        if (!root) return null;\n"
        "        const els = root.querySelectorAll('a,button,input,textarea,select,[role=button],[role=link],[onclick]');\n"
        "        const out = [];\n"
        "        for (const el of els) {\n"
        "          if (out.length >= a.limit) break;\n"
        "          const r = el.getBoundingClientRect();\n"
        "          if (!(r.width > 0 && r.height > 0)) continue;\n"
        "          const tag = el.tagName.toLowerCase();\n"
        "          const label = (el.getAttribute('aria-label') || el.value || el.innerText || el.getAttribute('placeholder') || '').trim().slice(0, 80);\n"
        "          let selector = '';\n"
        "          if (el.id) selector = '#' + CSS.escape(el.id);\n"
        "          else if (el.getAttribute('data-testid')) selector = '[data-testid=\"' + el.getAttribute('data-testid') + '\"]';\n"
        "          else if (el.getAttribute('name')) selector = tag + '[name=\"' + el.getAttribute('name') + '\"]';\n"
        "          else if (el.getAttribute('aria-label')) selector = tag + '[aria-label=\"' + el.getAttribute('aria-label') + '\"]';\n"
        "          out.push({ tag, type: el.getAttribute('type') || '', label, selector });\n"
        "        }\n"
        "        return { url: location.href, title: document.title, count: out.length, elements: out };\n"
        "      }, { rootSel: (sel === true ? null : sel), limit: limit || 60 });\n"
        "    }\n"
        "    for (const s of steps) {\n"
        "      if (s.goto !== undefined) { await page.goto(s.goto, { waitUntil: s.wait_until || 'domcontentloaded', timeout: 45000 }); results.push({ op: 'goto', url: page.url(), title: await page.title() }); }\n"
        "      else if (s.click !== undefined) { await page.click(s.click, { timeout: 10000 }); await page.waitForTimeout(300); results.push({ op: 'click', selector: s.click, url: page.url() }); }\n"
        "      else if (s.fill !== undefined) { await page.fill(s.fill, s.value != null ? String(s.value) : ''); results.push({ op: 'fill', selector: s.fill }); }\n"
        "      else if (s.type !== undefined) { await page.type(s.type, s.text != null ? String(s.text) : '', { delay: 10 }); results.push({ op: 'type', selector: s.type }); }\n"
        "      else if (s.press !== undefined) { if (s.selector) { await page.press(s.selector, s.press); } else { await page.keyboard.press(s.press); } await page.waitForTimeout(300); results.push({ op: 'press', key: s.press, url: page.url() }); }\n"
        "      else if (s.wait_for !== undefined) { await page.waitForSelector(s.wait_for, { timeout: s.timeout || 15000 }); results.push({ op: 'wait_for', selector: s.wait_for }); }\n"
        "      else if (s.wait !== undefined) { await page.waitForTimeout(s.wait); results.push({ op: 'wait', ms: s.wait }); }\n"
        "      else if (s.scroll !== undefined) { await page.evaluate((d) => { if (d === 'bottom') window.scrollTo(0, document.body.scrollHeight); else if (d === 'top') window.scrollTo(0, 0); else window.scrollBy(0, typeof d === 'number' ? d : 600); }, s.scroll); await page.waitForTimeout(200); results.push({ op: 'scroll', to: s.scroll }); }\n"
        "      else if (s.hover !== undefined) { await page.hover(s.hover, { timeout: 10000 }); results.push({ op: 'hover', selector: s.hover }); }\n"
        "      else if (s.select !== undefined) { await page.selectOption(s.select, s.value); results.push({ op: 'select', selector: s.select }); }\n"
        "      else if (s.text !== undefined) { let t; if (s.text === true) { t = await page.evaluate(() => document.body.innerText); } else { const el = await page.$(s.text); t = el ? await el.innerText() : null; } results.push({ op: 'text', selector: s.text === true ? null : s.text, found: t !== null, text: (t || '').slice(0, s.limit || 8000) }); }\n"
        "      else if (s.snapshot !== undefined) { const snap = await __snap(s.snapshot, s.limit); results.push(Object.assign({ op: 'snapshot' }, snap || { error: 'root selector not found' })); }\n"
        "      else if (s.eval !== undefined) { const v = await page.evaluate(s.eval); await page.waitForTimeout(200); results.push({ op: 'eval', value: (v === undefined ? null : v) }); }\n"
        "      else { results.push({ op: 'unknown', error: 'unrecognized step', step: s }); }\n"
        "    }\n"
        "    console.log(JSON.stringify({ status: 'ok', page_index: pageIndex, url: page.url(), title: await page.title(), results }));\n"
        "  } catch (e) {\n"
        "    console.log(JSON.stringify({ status: 'error', error: e.message }));\n"
        "  } finally {\n"
        "    if (browser) await browser.close();\n"
        "  }\n"
        "})();\n"
    )

    # Generous timeout: the whole sequence runs in one shot.
    return run_node(script, timeout=90, err_timeout="pw_act sequence timed out")

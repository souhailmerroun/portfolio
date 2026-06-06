"""
Get the HTML content of the page or a specific element.

By default the HTML is CLEANED (compact) before it's returned — scripts, styles,
SVGs, comments and noise attributes (class, style, data-*, event handlers, …) are
stripped and whitespace is collapsed. That keeps the navigable structure (ids,
names, roles, aria-labels, hrefs, data-testid) while removing the 70–90% of a
modern app's DOM that's pure token bloat. Pass clean=False for the raw DOM.

For *navigating* a page (what can I click/fill?), prefer `pw_snapshot` — it's even
cheaper. Use this when you need the actual structure/markup of a region.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node

# Attributes worth keeping in clean mode: selector-relevant + semantic. Everything
# else (class, style, data-* except data-testid, srcset, on*, …) is dropped.
_KEEP_ATTRS = ("id,name,type,role,href,value,placeholder,aria-label,aria-labelledby,"
               "for,title,alt,data-testid,checked,selected,disabled,contenteditable,"
               "colspan,rowspan,label")


def pw_get_html(selector: str = None, outer: bool = False, clean: bool = True, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Get the HTML content of the page or a specific element.

    Args:
        selector: CSS selector to get HTML from (optional, returns full page HTML if omitted)
        outer: If true, returns outerHTML (includes the element tag itself). If false, returns innerHTML (default: false)
        clean: If true (default), strip scripts/styles/svg/comments + noise attributes
            (class, style, data-*, event handlers) and collapse whitespace — far fewer
            tokens, structure preserved. Set false for the raw, byte-exact DOM.
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - html: The HTML content (truncated to 50000 chars if very long)
        - length: The full length of the (cleaned, if clean=True) HTML before truncation
        - cleaned: whether cleaning was applied
        - error: Error message if failed
    """
    sel_js = json.dumps(selector)          # JS string literal or null
    outer_js = "true" if outer else "false"
    resolve = resolve_page_js(page_index, page_url)

    if clean:
        body = (
            "const html = await page.evaluate(({ selector, outer, keep }) => {\n"
            "  const src = selector ? document.querySelector(selector) : document.documentElement;\n"
            "  if (!src) return null;\n"
            "  const root = src.cloneNode(true);\n"
            "  root.querySelectorAll('script,style,link,noscript,svg,template,canvas,iframe,meta,base,picture,source').forEach(n => n.remove());\n"
            "  const tw = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT, null);\n"
            "  const dead = []; while (tw.nextNode()) dead.push(tw.currentNode); dead.forEach(n => n.remove());\n"
            "  const KEEP = new Set(keep.split(','));\n"
            "  root.querySelectorAll('*').forEach(el => { for (const a of [...el.attributes]) if (!KEEP.has(a.name)) el.removeAttribute(a.name); });\n"
            "  let html = outer ? root.outerHTML : root.innerHTML;\n"
            "  return html.replace(/\\s+/g, ' ').replace(/>\\s+</g, '><').trim();\n"
            "}, { selector: " + sel_js + ", outer: " + outer_js + ", keep: " + json.dumps(_KEEP_ATTRS) + " });"
        )
    elif selector:
        loc = "page.locator(" + sel_js + ")"
        body = ("const html = await " + loc + ".evaluate(el => el.outerHTML);") if outer \
            else ("const html = await " + loc + ".innerHTML({ timeout: 10000 });")
    else:
        body = "const html = await page.content();"

    script = (
        "const { chromium } = require('playwright');\n"
        "(async () => {\n"
        "  let browser;\n"
        "  try {\n"
        "    browser = await chromium.connectOverCDP(" + json.dumps(cdp_url) + ");\n"
        "    const context = browser.contexts()[0];\n"
        + resolve + "\n"
        + "    " + body + "\n"
        "    if (html === null) { console.log(JSON.stringify({ status: 'error', error: 'selector not found: ' + " + sel_js + " })); return; }\n"
        "    const truncated = html.substring(0, 50000);\n"
        "    console.log(JSON.stringify({ status: 'ok', html: truncated, length: html.length, cleaned: " + ("true" if clean else "false") + " }));\n"
        "  } catch (e) {\n"
        "    console.log(JSON.stringify({ status: 'error', error: e.message }));\n"
        "  } finally {\n"
        "    if (browser) await browser.close();\n"
        "  }\n"
        "})();\n"
    )

    return run_node(script, timeout=30, err_timeout="Get HTML timed out")

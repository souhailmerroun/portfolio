"""Shared JS snippet to find a Playwright page by URL or index.

A target tab MUST be specified — either `page_index` or `page_url`. There is no
silent default to tab 0: port 9222 is the user's real browser, and defaulting to
tab 0 means navigating whatever tab the user is currently looking at (hijacking
their view). So if neither is given, the tool errors and tells the caller to pass
one. Callers that legitimately want the first tab pass `page_index=0` explicitly.
"""


def resolve_page_js(page_index=None, page_url: str = None) -> str:
    """Return JS code that sets `const page = ...` from either page_url or page_index.

    - page_url (preferred): finds the page whose URL contains the given string —
      stable across tab open/close, unlike a numeric index.
    - page_index: the tab by position. Pass it explicitly; there is NO default.
    - neither: returns JS that errors out (don't silently grab tab 0 = the user's tab).
    """
    if page_url:
        safe = page_url.replace("\\", "\\\\").replace("'", "\\'")
        return f"""
        const pages = context.pages();
        let page = pages.find(p => p.url().includes('{safe}'));
        if (!page) {{
            console.log(JSON.stringify({{ status: 'error', error: 'No page with URL containing \\'{safe}\\'' }}));
            return;
        }}"""
    elif page_index is None:
        # No target specified — refuse rather than default to tab 0 (the user's tab).
        return """
        console.log(JSON.stringify({ status: 'error', error: 'No target tab specified. Pass page_index=<n> (from pw_list_tabs) or page_url=<substring>. There is no default — tab 0 is the user\\'s active tab and must not be hijacked. Use pw_list_tabs to find your worker tab, or pw_new_tab to create one.' }));
        return;"""
    else:
        return f"""
        const pages = context.pages();
        if ({page_index} >= pages.length) {{
            console.log(JSON.stringify({{ status: 'error', error: 'page_index {page_index} out of range, only ' + pages.length + ' tabs open' }}));
            return;
        }}
        const page = pages[{page_index}];"""

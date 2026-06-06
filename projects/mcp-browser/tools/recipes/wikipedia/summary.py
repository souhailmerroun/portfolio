"""wikipedia — look up a topic and return its title + lead summary.

Parametrized read flow. Navigates Wikipedia's "Go" search (jumps straight to the
exact article when one exists, otherwise lands on the search-results page), then
returns the article title and the lead paragraph — the bit you actually want when
asking "what is X". No login, very stable DOM.

  pw_recipe(name="wikipedia/summary", params={"query": "Alan Turing"})
  pw_recipe(name="wikipedia/summary", params={"query": "Tour Eiffel", "lang": "fr"})
"""
from urllib.parse import quote

from tools.browser.playwright.pw_act import pw_act

MUTATES = False  # read-only


def run(query, lang: str = "en"):
    """Look up `query` on Wikipedia and return title + lead summary.

    Args:
        query: the topic to search (e.g. "Alan Turing").
        lang: Wikipedia language subdomain (default "en"; e.g. "fr", "de").
    """
    if not query or not str(query).strip():
        return {"status": "error", "error": "query is required"}
    url = (f"https://{lang}.wikipedia.org/wiki/Special:Search"
           f"?search={quote(str(query))}&go=Go")
    return pw_act(steps=[
        {"goto": url},
        {"wait_for": "#firstHeading"},
        {"text": "#firstHeading", "limit": 200},                       # article title
        {"text": ".mw-parser-output > p:not(.mw-empty-elt)", "limit": 1500},  # lead paragraph
    ], new_tab=True)

"""the-internet.herokuapp.com — log into the secure area.

The canonical UI-automation sandbox. Deterministic creds (tomsmith /
SuperSecretPassword!); the success signal is the `.flash.success` banner
("You logged into a secure area!"). Read-only sandbox — no real account, no
mutation — so it's the worked example of the compiled-recipe pattern: a whole
goto -> fill -> fill -> click -> verify flow in one pw_act call / one model turn.
"""
from tools.browser.playwright.pw_act import pw_act

MUTATES = False  # sandbox login; no real state change


def run(page_url: str = None):
    """Log in and return the success banner + a snapshot of the secure area.

    Args:
        page_url: reuse an existing tab whose URL contains this substring;
                  omit to run in a fresh worker tab.
    """
    kwargs = {"page_url": page_url} if page_url else {"new_tab": True}
    return pw_act(steps=[
        {"goto": "https://the-internet.herokuapp.com/login"},
        {"wait_for": "#username"},
        {"fill": "#username", "value": "tomsmith"},
        {"fill": "#password", "value": "SuperSecretPassword!"},
        {"click": "button[type='submit']"},
        {"wait_for": ".flash.success"},
        {"text": ".flash.success", "limit": 200},
        {"snapshot": True, "limit": 8},
    ], **kwargs)

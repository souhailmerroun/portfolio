"""
Change viewport size and device emulation settings.
"""
import subprocess
import json
import os

from tools.browser.config import REMOTE_CHROME_DIR
from tools.browser.playwright._resolve_page import resolve_page_js
from tools.browser.playwright._cdp import run_node

DEVICES = {
    "iphone-14": {"width": 390, "height": 844, "device_scale_factor": 3, "is_mobile": True, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"},
    "iphone-14-pro-max": {"width": 430, "height": 932, "device_scale_factor": 3, "is_mobile": True, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"},
    "pixel-7": {"width": 412, "height": 915, "device_scale_factor": 2.625, "is_mobile": True, "user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"},
    "ipad-pro": {"width": 1024, "height": 1366, "device_scale_factor": 2, "is_mobile": True, "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"},
    "desktop-hd": {"width": 1920, "height": 1080, "device_scale_factor": 1, "is_mobile": False, "user_agent": None},
    "desktop-4k": {"width": 3840, "height": 2160, "device_scale_factor": 1, "is_mobile": False, "user_agent": None},
    "laptop": {"width": 1440, "height": 900, "device_scale_factor": 2, "is_mobile": False, "user_agent": None},
}


def pw_viewport(width: int = None, height: int = None, device: str = None, color_scheme: str = None, page_index: int = None, cdp_url: str = "http://localhost:9222", page_url: str = None) -> dict:
    """
    Change viewport size, emulate a device, or set color scheme (dark/light mode).

    Either specify width+height for a custom size, or use a device preset.

    Args:
        width: Viewport width in pixels (e.g., 1440)
        height: Viewport height in pixels (e.g., 900)
        device: Device preset name instead of width/height. Options: "iphone-14", "iphone-14-pro-max", "pixel-7", "ipad-pro", "desktop-hd", "desktop-4k", "laptop"
        color_scheme: Set color scheme preference - "dark", "light", or "no-preference" (optional)
        page_index: Which tab to use, by index — REQUIRED unless page_url is given; no default (tab 0 is the user's tab, never hijack it). From pw_list_tabs.
        cdp_url: The CDP endpoint URL of the running browser (default: "http://localhost:9222")

    Returns:
        A dictionary containing:
        - status: "ok" or "error"
        - viewport: The viewport dimensions that were set (width, height)
        - device: The device preset used (if any)
        - color_scheme: The color scheme set (if any)
        - error: Error message if failed
    """
    if device:
        if device not in DEVICES:
            return {"status": "error", "error": f"Unknown device '{device}'. Options: {', '.join(DEVICES.keys())}"}
        d = DEVICES[device]
        vp_width = d["width"]
        vp_height = d["height"]
        scale = d["device_scale_factor"]
        is_mobile = d["is_mobile"]
        ua = d["user_agent"]
    elif width and height:
        vp_width = width
        vp_height = height
        scale = 1
        is_mobile = False
        ua = None
    else:
        return {"status": "error", "error": "Provide either width+height or a device preset"}

    ua_code = ""
    if ua:
        safe_ua = ua.replace("'", "\\'")
        ua_code = f"""
        const cdpSession = await page.context().newCDPSession(page);
        await cdpSession.send('Emulation.setUserAgentOverride', {{ userAgent: '{safe_ua}' }});
        await cdpSession.send('Emulation.setTouchEmulationEnabled', {{ enabled: {str(is_mobile).lower()}, maxTouchPoints: 5 }});
        await cdpSession.send('Emulation.setDeviceMetricsOverride', {{
            width: {vp_width},
            height: {vp_height},
            deviceScaleFactor: {scale},
            mobile: {str(is_mobile).lower()}
        }});
"""

    color_code = ""
    color_result = "null"
    if color_scheme:
        color_code = f"""
        await page.emulateMedia({{ colorScheme: '{color_scheme}' }});
"""
        color_result = f"'{color_scheme}'"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    let browser;
    try {{
        browser = await chromium.connectOverCDP('{cdp_url}');
        const context = browser.contexts()[0];
        {resolve_page_js(page_index, page_url)}
        await page.setViewportSize({{ width: {vp_width}, height: {vp_height} }});
        {ua_code}
        {color_code}
        console.log(JSON.stringify({{
            status: 'ok',
            viewport: {{ width: {vp_width}, height: {vp_height} }},
            device_scale_factor: {scale},
            mobile: {str(is_mobile).lower()},
            device: {f"'{device}'" if device else "null"},
            color_scheme: {color_result}
        }}));
    }} catch (e) {{
        console.log(JSON.stringify({{ status: 'error', error: e.message }}));
    }} finally {{
        if (browser) await browser.close();
    }}
}})();
"""
    return run_node(script, timeout=15, err_timeout="Viewport change timed out")

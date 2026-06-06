"""
Optimize a screenshot for storage and LLM readability.

Caps the longest side at 1568px (Anthropic vision sweet spot, well under
the 2000px conversation limit) and converts to JPEG at 75% quality.
Replaces the original file in-place.
"""
from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # disable decompression bomb limit for large full-page screenshots

JPEG_QUALITY = 75
MAX_DIMENSION = 1568


def optimize_screenshot(path: str) -> None:
    """
    Resize (longest side ≤ MAX_DIMENSION) and re-encode in-place as JPEG.

    Args:
        path: Path to the screenshot to optimize
    """
    try:
        with Image.open(path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            longest = max(img.size)
            if longest > MAX_DIMENSION:
                scale = MAX_DIMENSION / longest
                new_size = (round(img.size[0] * scale), round(img.size[1] * scale))
                img = img.resize(new_size, Image.LANCZOS)
            img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    except Exception:
        pass

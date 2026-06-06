import os

# Path to the playwright-runtime directory (contains package.json + node_modules).
# Override with MCP_PLAYWRIGHT_RUNTIME env var; defaults to playwright-runtime/
# next to this repo's root.
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REMOTE_CHROME_DIR = os.environ.get(
    "MCP_PLAYWRIGHT_RUNTIME",
    os.path.join(_repo_root, "playwright-runtime"),
)

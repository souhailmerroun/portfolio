# Usage

Each project under `projects/` is set up and run independently — there's no top-level install command. First, do the one-time repo-level hook setup, then follow the per-project instructions below.

## Repo-level setup (once per clone)

```sh
git clone <repo-url> && cd career-portfolio
./.hooks/setup.sh
```

This sets `core.hooksPath = .hooks` (enabling `pre-commit`/`pre-push` checks) and installs a global `git ship` alias for the branch → PR → squash-merge workflow described in [`.hooks/README.md`](../.hooks/README.md).

---

## mcp-browser

**Prerequisites**: Python 3.10+, Node.js 18+, and a Chromium-family browser running with `--remote-debugging-port=9222` (Arc on macOS does this automatically; otherwise `chromium --remote-debugging-port=9222`).

```sh
cd projects/mcp-browser

# Python deps
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Node Playwright runtime
cd playwright-runtime && npm install && cd ..
```

Register it as an MCP server (e.g. in `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-browser": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "server"],
      "cwd": "/path/to/mcp-browser",
      "env": { "MCP_PLAYWRIGHT_RUNTIME": "/path/to/mcp-browser/playwright-runtime" }
    }
  }
}
```

Or run it standalone:

```sh
python server.py
```

Once connected, a typical agent session opens a new tab (never tab 0, which is reserved for the user), navigates, inspects the page via `pw_snapshot`, then acts — or collapses the whole flow into one `pw_act` call. See [`projects/mcp-browser/README.md`](../projects/mcp-browser/README.md) for the full tool list and a worked example.

---

## no-claude-no-job

**Prerequisites**: Node.js (for Next.js 16 / React 19).

```sh
cd projects/no-claude-no-job
npm install
npm run dev      # http://localhost:3000
```

Other scripts: `npm run build`, `npm run start`. The app is deployed on Vercel at [no-claude-no-job.vercel.app](https://no-claude-no-job.vercel.app) — no environment variables or backing services are required; the only external dependency is the public Anthropic status endpoint, proxied server-side through `app/api/status/route.ts`.

---

## rag-indexer

**Prerequisites**: Python 3.12+, and a local [Ollama](https://ollama.com) instance with the embedding model pulled.

```sh
cd projects/rag-indexer

ollama pull nomic-embed-text
pip install -r requirements.txt
```

Edit `config.json` to point `roots` at the directories you want indexed (it defaults to `./example-docs` and only picks up `README.md` files and anything under `/docs/`).

```sh
python indexer.py index                              # incremental index
python indexer.py search "how does authentication work" -k 5
python indexer.py reindex                             # drop + rebuild the collection
python indexer.py status                              # chunk count, indexed files
```

Re-running `index` is cheap: files are SHA-256 hashed, so only changed content gets re-embedded and re-upserted into ChromaDB.

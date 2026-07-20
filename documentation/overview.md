# Overview

`career-portfolio` is Souhail Merroun's portfolio repository: a monorepo of three independent, self-contained personal projects, each in its own directory under `projects/`. It exists to showcase working software in the AI/agentic-systems and full-stack space — not as a single deployable product.

There is no shared runtime or shared codebase between the projects. Each has its own language stack, dependency manifest, and README. What the repo provides at the top level is: an index (this README/documentation), and shared repo hygiene tooling (git hooks in `.hooks/`).

## The three projects

### mcp-browser

**What**: An MCP (Model Context Protocol) server, built on [FastMCP](https://github.com/jlowin/fastmcp), that exposes browser automation as callable tools for an AI agent (e.g. Claude via Claude Desktop). It wraps Playwright with 30+ primitives (`pw_goto`, `pw_click`, `pw_fill`, `pw_snapshot`, `pw_screenshot`, `pw_act`, ...) plus Arc-browser-specific tab tools.

**Why it's interesting**: Two design decisions stand out —
1. A persistent CDP (Chrome DevTools Protocol) daemon (`cdp_daemon.js`) holds one live browser connection so repeated tool calls skip the ~300-800ms handshake a fresh connection would cost.
2. `pw_act` batches a whole action sequence (goto → fill → click → snapshot) into a single MCP round-trip, which matters a lot in agentic loops where each round-trip also costs LLM latency.

It also enforces a hard invariant — tools refuse to default to tab index 0, which is reserved for the human's own active browser tab.

### no-claude-no-job

**What**: A Next.js 16 / React 19 app that polls `status.anthropic.com` server-side (via an API route, to dodge CORS) every 60 seconds. When Claude is fully operational the game is locked; during an incident it unlocks a coding-challenge game — one-liner fill-in-the-blank challenges across 12 languages (JS, TS, React, Python, PHP, Go, Rust, Java, C#, Ruby, Bash, SQL).

**Why it's interesting**: It's a small, complete, deployed (Vercel) product — server component for layout, client component for game state (no reducer, just a conditional-render state machine), whitespace-insensitive answer normalization, and a client-side Canvas-generated 1200x630 share image with no server round-trip.

### rag-indexer

**What**: A ~200-line single-file Python CLI (`indexer.py`) for local semantic search over a codebase's documentation. It walks configured root directories, filters/chunks markdown and JSON files, embeds chunks with Ollama's `nomic-embed-text` model, and stores/searches vectors in ChromaDB.

**Why it's interesting**: Content-hash (SHA-256) based incremental indexing means re-running `index` only re-embeds files that actually changed. Embedding calls fan out over a thread pool (`embed_parallel` in `config.json`). Symlinked files are deduplicated via `realpath` resolution before indexing so the same file isn't indexed twice under different paths.

## What ties them together

All three are exercises in making AI agents (or AI-adjacent workflows) faster and more capable: giving an agent a browser (mcp-browser), giving a human something to do only when their AI agent is unavailable (no-claude-no-job), and giving an agent/human fast semantic recall over documentation instead of grepping (rag-indexer).

See [`structure.md`](structure.md) for the concrete file layout and [`usage.md`](usage.md) for how to set up and run each project.

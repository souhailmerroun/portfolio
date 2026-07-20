# career-portfolio

Souhail Merroun's portfolio repository — Senior Full-Stack Engineer (React / TypeScript / AI & Agentic Systems). A monorepo holding three independent personal projects, each showcasing a different slice of the AI/agentic-systems and full-stack space.

## Overview

This repo is not a single application — it's a container for standalone projects, each living in its own directory under `projects/` with its own dependencies, README, and (where relevant) deployment. What ties them together is the theme: building tools that let AI agents (and people) do things faster — drive a browser, search documentation semantically, or just kill time while Claude is down.

## Projects

### [`projects/mcp-browser/`](projects/mcp-browser/) — agentic browser automation via MCP

A [FastMCP](https://github.com/jlowin/fastmcp) server exposing 30+ Playwright browser tools (`pw_goto`, `pw_click`, `pw_fill`, `pw_snapshot`, `pw_act`, ...) to MCP clients like Claude, so an agent can drive a real browser tab-by-tab without touching the user's active tab. Includes a persistent Chrome DevTools Protocol (CDP) daemon that keeps one live connection open to eliminate per-call handshake latency, an auto-discovery tool registry (drop a `.py` file in `tools/` and it's live), Arc-browser tab management, and a `pw_recipe` dispatcher for pre-verified multi-step flows.

- Stack: Python (FastMCP, Playwright, watchdog), Node.js (CDP daemon)
- Entry point: `server.py`

### [`projects/no-claude-no-job/`](projects/no-claude-no-job/) — a coding challenge game that only unlocks when Claude is down

A Next.js app that polls Anthropic's status page every 60 seconds. While Claude is operational the game is locked; when there's an incident it unlocks and throws programming one-liners at you across 12 languages, with answer normalization and client-side (Canvas API) share-image generation.

- Stack: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, deployed on Vercel
- Live: [no-claude-no-job.vercel.app](https://no-claude-no-job.vercel.app)

### [`projects/rag-indexer/`](projects/rag-indexer/) — local semantic search over codebase documentation

A single-file Python CLI (`indexer.py`) that walks a repo tree, chunks markdown/JSON docs, embeds them with `nomic-embed-text` via a local Ollama instance, and stores the vectors in ChromaDB for cosine-similarity search. Incremental indexing via SHA-256 content hashing means only changed files get re-embedded.

- Stack: Python 3.12+, ChromaDB, Ollama
- Commands: `index`, `reindex`, `search`, `status`

## Repo-level tooling

### `.hooks/`

Git hooks shipped with the repo (`pre-commit`, `pre-push`) applied via `core.hooksPath = .hooks`. They block direct commits/pushes to `main`, `.env` files, `.DS_Store`, secrets, oversized files, and missing version bumps. Run once per clone:

```sh
./.hooks/setup.sh
```

This also installs a global `git ship` alias (feature branch → push → PR → squash-merge → back on updated `main`). See [`.hooks/README.md`](.hooks/README.md) for details.

## Setup

There is no single build for the whole repo — each project under `projects/` is set up and run independently. See each project's own README for exact steps:

- [`projects/mcp-browser/README.md`](projects/mcp-browser/README.md)
- [`projects/no-claude-no-job/README.md`](projects/no-claude-no-job/README.md)
- [`projects/rag-indexer/README.md`](projects/rag-indexer/README.md)

General pattern:

```sh
git clone <repo-url> && cd career-portfolio
./.hooks/setup.sh          # once per clone — enables repo hooks + git ship alias
cd projects/<project-name> # then follow that project's README
```

## Documentation

Deeper, cross-cutting documentation lives in [`documentation/`](documentation/) — start at the [table of contents](documentation/table-of-contents.md).

## Contact

- GitHub: [souhailmerroun](https://github.com/souhailmerroun)
- Malt: [malt.fr/profile/souhailmerroun](https://www.malt.fr/profile/souhailmerroun)

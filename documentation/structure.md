# Structure

## Top level

```
career-portfolio/
├── README.md                 Repo index — one-line summary of each project
├── documentation/            This folder — cross-cutting docs
├── .hooks/                   Shared git hooks (pre-commit, pre-push) + setup script
└── projects/
    ├── mcp-browser/
    ├── no-claude-no-job/
    └── rag-indexer/
```

The three entries under `projects/` are independent — no shared `package.json`, no shared virtualenv, no build orchestration across them. Each is documented in its own README (`projects/<name>/README.md`).

## `.hooks/`

```
.hooks/
├── README.md      Explains each hook and the branch/PR workflow
├── setup.sh        Run once per clone: sets core.hooksPath, installs `git ship` alias
├── pre-commit       Blocks: direct commits to main, .env files, .DS_Store, merge
│                    conflict markers, invalid JSON, files >10MB, secret patterns,
│                    inline JS/CSS in HTML, oversized files, missing version bumps
└── pre-push         Blocks: direct pushes to main, force-pushes to any branch
```

This repo enforces a "main is merge-only" workflow: work happens on short-lived feature branches, shipped via the `git ship` alias installed by `setup.sh` (push → open PR → squash-merge → return to updated `main`).

## `projects/mcp-browser/`

```
mcp-browser/
├── README.md
├── server.py                 3-line FastMCP entry point
├── server_base.py            Factory: auto-discovers tools, starts file watcher
├── tools_registry.py         Walks tools/, registers every non-private function as an MCP tool
├── requirements.txt          fastmcp, watchdog, playwright, Pillow, nest_asyncio, mcp-hmr
├── tools/
│   ├── browser/
│   │   ├── config.py         MCP_PLAYWRIGHT_RUNTIME env var (path to Node runtime)
│   │   ├── recipe.py         pw_recipe dispatcher
│   │   ├── playwright/       One file per pw_* tool (pw_goto, pw_click, pw_fill, ...)
│   │   │   ├── _cdp.py       Persistent CDP daemon bridge
│   │   │   ├── cdp_daemon.js Long-lived Node daemon reusing one CDP connection
│   │   │   └── _resolve_page.py  Shared JS: resolve a page by index or URL substring
│   │   └── arc/               Arc-browser tab management (fetch/open/close/navigate tabs)
│   └── recipes/
│       ├── the_internet/login.py    Pre-verified login flow (UI-automation sandbox)
│       └── wikipedia/summary.py     Pre-verified article-summary fetch
└── playwright-runtime/
    └── package.json          Node runtime dependency: playwright ^1.58.2
```

Key pattern: **one tool = one file.** `tools_registry.py` auto-discovers every non-underscore `.py` file under `tools/` at startup — adding a new browser tool is just dropping in a new file, no registration boilerplate.

## `projects/no-claude-no-job/`

```
no-claude-no-job/
├── README.md
├── package.json               next 16, react 19, react-dom 19, tailwindcss 4, typescript 5
├── next.config.ts / tsconfig.json / postcss.config.mjs
├── app/
│   ├── layout.tsx              Root layout (Geist font, metadata)
│   ├── page.tsx                Game UI — state via useState/useEffect
│   ├── challenges.ts           Challenge bank + answer normalizer
│   ├── globals.css             Tailwind base
│   └── api/status/route.ts     Server-side proxy to status.anthropic.com (avoids CORS)
└── public/                     Static SVG assets (Next.js defaults)
```

The status check is server-side (API route) specifically to avoid CORS issues hitting Anthropic's status endpoint directly from the browser. Everything else (game state, timers, answer checking) is client-side — no database, no auth.

## `projects/rag-indexer/`

```
rag-indexer/
├── README.md
├── requirements.txt           chromadb, requests
├── config.json                roots, excludes, include_only, extensions, chunk_size,
│                               chunk_overlap, embed_model, embed_parallel, chroma_path
└── indexer.py                 Single-file CLI: index / reindex / search / status
```

`config.json` as shipped points `roots` at `./example-docs` and restricts `include_only` to `README.md` files and anything under a `/docs/` path — this is the sample/default configuration; point `roots` at real repositories to index them.

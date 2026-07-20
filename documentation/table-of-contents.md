# career-portfolio — table of contents

## Documentation

- [Overview](overview.md) — what this repo is, the three projects it contains, and why each exists
- [Structure](structure.md) — top-level layout plus a file-by-file breakdown of each project directory
- [Usage](usage.md) — setup and run instructions for the repo hooks and each of the three projects

## Repo map

```
career-portfolio/
├── README.md              Repo index — one-line summary of each project + links
├── documentation/         You are here
├── .hooks/                Shared git hooks (pre-commit, pre-push) + setup.sh
└── projects/
    ├── mcp-browser/        MCP server exposing Playwright browser automation as agent tools
    ├── no-claude-no-job/   Next.js coding-challenge game that unlocks during Claude outages
    └── rag-indexer/        Python CLI for local semantic search over markdown docs (Ollama + ChromaDB)
```

Each project directory also has its own `README.md` with project-specific detail beyond what's summarized here.

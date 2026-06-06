# Portfolio — Souhail Merroun

Senior Full-Stack Engineer — React / TypeScript / AI & Agentic Systems

## Projects

### mcp-browser

**Agentic browser automation via MCP (Model Context Protocol)**

A FastMCP server powering 30+ Playwright browser tools for autonomous AI agents. Persistent CDP daemon eliminates per-call latency. Used daily in production agentic pipelines.

- **Stack**: Python, Node.js, Playwright, FastMCP, Chrome DevTools Protocol
- **Highlights**: auto-discovery tool registry, tab-safety invariant, `pw_act` batch executor for multi-step flows in one LLM round-trip
- **Code**: [`projects/mcp-browser/`](projects/mcp-browser/)

### no-claude-no-job

**A coding challenge game you can only play when Claude is down**

Next.js app that polls Anthropic's status page — locked while Claude is operational, unlocks during incidents. Throws programming one-liners across 12 languages with answer normalization and client-side share image generation.

- **Stack**: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- **Highlights**: server-side status proxy, Canvas API for OG image rendering, deployed on Vercel
- **Live**: [no-claude-no-job.vercel.app](https://no-claude-no-job.vercel.app)
- **Code**: [`projects/no-claude-no-job/`](projects/no-claude-no-job/)

### rag-indexer

**Local semantic search over codebase documentation**

CLI tool that walks a repo tree, chunks markdown docs, embeds them via Ollama (`nomic-embed-text`), and stores vectors in ChromaDB. Incremental indexing via content hashing — only changed files get re-embedded.

- **Stack**: Python, ChromaDB, Ollama, nomic-embed-text
- **Highlights**: SHA-256 content dedup, parallel embedding, cosine similarity search, symlink-aware deduplication
- **Code**: [`projects/rag-indexer/`](projects/rag-indexer/)

---

## Contact

- GitHub: [souhailmerroun](https://github.com/souhailmerroun)
- Malt: [malt.fr/profile/souhailmerroun](https://www.malt.fr/profile/souhailmerroun)

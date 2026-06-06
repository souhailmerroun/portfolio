# rag-indexer

Local semantic search over a codebase's documentation. Embeds markdown chunks with `nomic-embed-text` via Ollama, stores them in ChromaDB, and queries with cosine similarity.

Point it at any repo (or set of repos) and ask natural-language questions like *"where does the expense schema live?"* instead of grepping.

## How it works

```
walk roots ─→ filter ─→ SHA-256 hash ─→ skip if unchanged
                                          │
                                          └─→ chunk (500 words, 50 overlap)
                                              → parallel embed (n workers)
                                              → ChromaDB upsert
```

**Search** embeds the query, runs a cosine-similarity nearest-neighbor lookup against the vector store, and returns the top-k chunks with file path, chunk index, and score.

## Usage

```sh
# Prerequisites: Ollama running locally with nomic-embed-text pulled
ollama pull nomic-embed-text

# Install
pip install -r requirements.txt

# Index (incremental — skips unchanged files via content hash)
python indexer.py index

# Search
python indexer.py search "how does authentication work" -k 5

# Full reindex (drops + rebuilds the collection)
python indexer.py reindex

# Status (chunk count, indexed file list)
python indexer.py status
```

## Configuration

All tuning in `config.json`:

| Key | What it controls |
|---|---|
| `roots` | Directories to walk |
| `excludes` | Directory/file names to skip (`node_modules`, `.git`, etc.) |
| `include_only` | Allowlist by filename or path substring (e.g. only `README.md` + `/docs/`) |
| `extensions` | File extensions to index (`.md`, `.json`) |
| `chunk_size` / `chunk_overlap` | Word-level chunking parameters |
| `embed_model` | Ollama model name for embeddings |
| `embed_parallel` | Concurrent embedding requests |
| `chroma_path` | On-disk ChromaDB location |

## Architecture

Single-file CLI (`indexer.py`, ~200 lines) with four commands: `index`, `reindex`, `search`, `status`.

**Key design decisions:**

- **Content-hash deduplication**: SHA-256 of file contents means re-running `index` is cheap — only changed files get re-embedded.
- **Cosine over L2**: `nomic-embed-text` embeddings aren't unit-normalized; cosine produces readable 0–1 similarity scores.
- **Parallel embedding**: ThreadPoolExecutor fans out embedding HTTP calls to Ollama, configurable via `embed_parallel`.
- **Realpath deduplication**: symlinks pointing to the same file are resolved before indexing, preventing duplicate chunks in search results.
- **Word-level chunking with overlap**: 500-word chunks fit most doc files in one piece; 50-word overlap preserves context at boundaries.

## Stack

- **Python 3.12+**
- **ChromaDB** — persistent vector store with HNSW index
- **Ollama** — local embedding inference (`nomic-embed-text`)
- **requests** — HTTP client for Ollama API

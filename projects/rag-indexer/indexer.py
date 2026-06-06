#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import chromadb
import requests

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text())


def embed(text: str) -> list[float] | None:
    try:
        r = requests.post(
            f"{CONFIG['ollama_url']}/api/embeddings",
            json={"model": CONFIG["embed_model"], "prompt": text},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        print(f"  embed failed: {e}", file=sys.stderr)
        return None


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [text] if text.strip() else []
    chunks = []
    step = max(1, size - overlap)
    for i in range(0, len(words), step):
        piece = " ".join(words[i : i + size])
        if piece.strip():
            chunks.append(piece)
        if i + size >= len(words):
            break
    return chunks


def matches_include(path: Path) -> bool:
    rule = CONFIG.get("include_only")
    if not rule:
        return True
    if path.name in set(rule.get("filenames", [])):
        return True
    p = str(path)
    return any(needle in p for needle in rule.get("path_contains", []))


def iter_files():
    exts = set(CONFIG["extensions"])
    excludes = set(CONFIG["excludes"])
    max_bytes = CONFIG["max_file_size_kb"] * 1024
    seen = set()
    for root in CONFIG["roots"]:
        root = os.path.realpath(os.path.expanduser(root))
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirnames[:] = [d for d in dirnames if d not in excludes]
            for name in filenames:
                if name in excludes:
                    continue
                path = Path(os.path.realpath(Path(dirpath) / name))
                if path in seen:
                    continue
                if path.suffix.lower() not in exts:
                    continue
                if not matches_include(path):
                    continue
                try:
                    if path.stat().st_size > max_bytes:
                        continue
                except OSError:
                    continue
                seen.add(path)
                yield path


def get_collection():
    chroma_path = (ROOT / CONFIG["chroma_path"]).resolve()
    client = chromadb.PersistentClient(path=str(chroma_path))
    return client.get_or_create_collection(
        CONFIG["collection"],
        metadata={"hnsw:space": "cosine"},
    )


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def cmd_index(args):
    col = get_collection()
    indexed = 0
    skipped = 0
    chunks_total = 0
    for path in iter_files():
        h = file_hash(path)
        existing = col.get(where={"file": str(path)}, include=["metadatas"])
        if existing["ids"] and all(
            m.get("hash") == h for m in existing["metadatas"]
        ):
            skipped += 1
            continue
        if existing["ids"]:
            col.delete(ids=existing["ids"])
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"skip {path}: {e}", file=sys.stderr)
            continue
        chunks = chunk_text(text, CONFIG["chunk_size"], CONFIG["chunk_overlap"])
        if not chunks:
            continue
        ids, embeds, metas, docs = [], [], [], []
        n_parallel = max(1, CONFIG.get("embed_parallel", 1))
        with ThreadPoolExecutor(max_workers=n_parallel) as ex:
            results = list(ex.map(embed, chunks))
        for i, (chunk, v) in enumerate(zip(chunks, results)):
            if v is None:
                continue
            ids.append(f"{h}:{i}")
            embeds.append(v)
            metas.append({"file": str(path), "chunk": i, "hash": h})
            docs.append(chunk)
        if not ids:
            continue
        col.add(ids=ids, embeddings=embeds, metadatas=metas, documents=docs)
        indexed += 1
        chunks_total += len(chunks)
        print(f"indexed {path} ({len(chunks)} chunks)")
    print(f"\ndone: {indexed} files indexed, {skipped} unchanged, {chunks_total} new chunks")


def cmd_search(args):
    col = get_collection()
    q_embed = embed(args.query)
    res = col.query(query_embeddings=[q_embed], n_results=args.k)
    if not res["ids"][0]:
        print("no results")
        return
    for rank, (doc, meta, dist) in enumerate(
        zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1
    ):
        score = 1 - dist
        snippet = doc.replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        print(f"\n[{rank}] score={score:.3f}  {meta['file']}#chunk{meta['chunk']}")
        print(f"    {snippet}")


def cmd_reindex(args):
    col = get_collection()
    chroma_path = (ROOT / CONFIG["chroma_path"]).resolve()
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        client.delete_collection(CONFIG["collection"])
    except Exception:
        pass
    cmd_index(args)


def cmd_status(args):
    col = get_collection()
    count = col.count()
    files = set()
    if count:
        all_metas = col.get(include=["metadatas"])["metadatas"]
        files = {m["file"] for m in all_metas}
    print(f"collection: {CONFIG['collection']}")
    print(f"chunks: {count}")
    print(f"files: {len(files)}")
    for f in sorted(files):
        print(f"  {f}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index").set_defaults(func=cmd_index)
    sub.add_parser("reindex").set_defaults(func=cmd_reindex)
    sub.add_parser("status").set_defaults(func=cmd_status)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=5)
    s.set_defaults(func=cmd_search)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

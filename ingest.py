"""Ingest docs/knowledge/ into Chroma. Supports one-shot and file-watch modes."""
from __future__ import annotations
import argparse
import hashlib
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from vectordb import get_collection, PROJECT_ROOT

KNOWLEDGE_DIR = PROJECT_ROOT / "docs" / "knowledge"
SUPPORTED = {".md", ".markdown", ".txt"}
CHUNK_TOKENS = 500
CHUNK_OVERLAP = 50  # ~10%


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_text(text: str, size: int = CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Paragraph-aware chunker. Groups paragraphs until ~size tokens, with overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    buf_tokens = 0
    for p in paragraphs:
        t = _approx_tokens(p)
        if buf and buf_tokens + t > size:
            chunks.append("\n\n".join(buf))
            # overlap: carry the last paragraph forward if it fits
            carry = buf[-1] if _approx_tokens(buf[-1]) <= overlap * 2 else ""
            buf = [carry] if carry else []
            buf_tokens = _approx_tokens(carry)
        buf.append(p)
        buf_tokens += t
    if buf:
        chunks.append("\n\n".join(buf))
    return [c for c in chunks if c.strip()]


def _chunk_id(doc_path: Path, idx: int, content: str) -> str:
    h = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"{doc_path.stem}:{idx}:{h}"


def ingest_file(path: Path, collection) -> int:
    if path.suffix.lower() not in SUPPORTED:
        return 0
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return 0
    chunks = chunk_text(text)
    ids, docs, metas = [], [], []
    for i, chunk in enumerate(chunks):
        ids.append(_chunk_id(path, i, chunk))
        docs.append(chunk)
        metas.append({
            "source": str(path.relative_to(PROJECT_ROOT)),
            "doc_name": path.stem,
            "doc_type": _infer_doc_type(path.stem),
            "chunk_index": i,
            "mtime": int(path.stat().st_mtime),
        })
    # delete any prior chunks for this doc then upsert
    collection.delete(where={"doc_name": path.stem})
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(chunks)


def _infer_doc_type(stem: str) -> str:
    s = stem.lower()
    if "brand" in s or "voice" in s:
        return "brand"
    if "icp" in s or "persona" in s or "customer" in s:
        return "icp"
    if "postmortem" in s or "retro" in s or "learning" in s:
        return "postmortem"
    if "strategy" in s or "plan" in s:
        return "strategy"
    if "competitor" in s:
        return "competitor"
    return "general"


def ingest_all(collection) -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    files = [p for p in KNOWLEDGE_DIR.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED]
    total = 0
    for f in files:
        n = ingest_file(f, collection)
        total += n
        print(f"  ingested {n:3d} chunks  ·  {f.relative_to(PROJECT_ROOT)}")
    print(f"\nDone. {len(files)} files, {total} chunks. Collection size: {collection.count()}")


class _Handler(FileSystemEventHandler):
    def __init__(self, collection):
        self.collection = collection
        self._last = 0.0

    def _debounced(self, path: Path):
        now = time.time()
        if now - self._last < 0.5:
            return
        self._last = now
        try:
            n = ingest_file(path, self.collection)
            if n:
                print(f"[watch] reindexed {path.name} ({n} chunks)")
        except Exception as e:  # pragma: no cover
            print(f"[watch] error on {path}: {e}", file=sys.stderr)

    def on_modified(self, event):
        if not event.is_directory:
            self._debounced(Path(event.src_path))

    def on_created(self, event):
        if not event.is_directory:
            self._debounced(Path(event.src_path))

    def on_deleted(self, event):
        if event.is_directory:
            return
        stem = Path(event.src_path).stem
        self.collection.delete(where={"doc_name": stem})
        print(f"[watch] deleted chunks for {stem}")


def watch(collection) -> None:
    print(f"[watch] {KNOWLEDGE_DIR} — Ctrl+C to exit")
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(_Handler(collection), str(KNOWLEDGE_DIR), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="Watch docs/knowledge/ for changes")
    args = ap.parse_args()

    collection = get_collection()
    print(f"Initial ingest from {KNOWLEDGE_DIR}…")
    ingest_all(collection)
    if args.watch:
        watch(collection)


if __name__ == "__main__":
    main()

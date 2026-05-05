from langchain_core.tools import tool
from vectordb import get_collection


@tool
def knowledge_search(query: str, k: int = 3, doc_type: str | None = None) -> str:
    """Semantic search over the internal marketing knowledge base (Chroma).

    Use this BEFORE hitting the web for:
      - brand voice / tone / guidelines
      - past campaign post-mortems and learnings
      - ICP / persona / customer profile
      - prior strategy decisions

    Args:
        query: natural-language query.
        k: number of chunks to return (default 5, max 10).
        doc_type: optional filter. One of: brand, icp, postmortem, strategy,
                  competitor, general. Leave None to search across all.

    Returns:
        Markdown-formatted top-k chunks with source and relevance.
    """
    k = max(1, min(int(k), 10))
    where = {"doc_type": doc_type} if doc_type else None
    collection = get_collection()
    if collection.count() == 0:
        return "Knowledge base is empty. Run `python ingest.py` to populate it."
    res = collection.query(query_texts=[query], n_results=k, where=where)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    if not docs:
        return f"No matches for: {query!r}" + (f" (filter doc_type={doc_type})" if doc_type else "")
    parts = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
        score = 1 - float(dist)  # cosine distance → similarity
        parts.append(
            f"### Result {i}  ·  {meta.get('source','?')}  ·  "
            f"type={meta.get('doc_type','?')}  ·  similarity={score:.3f}\n{doc}"
        )
    return "\n\n".join(parts)

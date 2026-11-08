"""Search Amazon products and answer from the results.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.
The index is built by src/amazon/eval_products.py (bge-m3, Chroma, one document per product).
"""
from langchain_core.messages import HumanMessage, SystemMessage

from src.amazon.eval_products import build_product_index, get_embeddings
from src.amazon.load_esci import load_query_ids


def text_of(response) -> str:
    """Gemini can return a list of parts instead of a string. Join the text parts."""
    content = response.content
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content.strip()


def open_index():
    embeddings = get_embeddings()
    return build_product_index(embeddings, load_query_ids()), embeddings


def search(query: str, collection, embeddings, top_k: int = 10) -> list[dict]:
    found = collection.query(query_embeddings=[embeddings.embed_query(query)], n_results=top_k)
    return [
        {"rank": rank, "product_id": pid, "title": meta["title"], "document": doc, "score": round(1 - dist, 4)}
        for rank, (pid, meta, doc, dist) in enumerate(
            zip(found["ids"][0], found["metadatas"][0], found["documents"][0], found["distances"][0]), start=1
        )
    ]


def generate_answer(query: str, results: list[dict], llm) -> str:
    context = "\n\n".join(f"[{r['product_id']}] {r['document']}" for r in results)
    response = llm.invoke([
        SystemMessage(content=(
            "You are a shopping assistant. Recommend products using only the context. "
            "Cite product IDs in brackets. Answer briefly, in the user's language. If nothing fits, say so."
        )),
        HumanMessage(content=f"Context:\n{context}\n\nRequest: {query}"),
    ])
    return text_of(response)

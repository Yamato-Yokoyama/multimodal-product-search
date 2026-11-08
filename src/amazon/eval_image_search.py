"""Evaluate image search with a product photo as the query.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.

For each plain query, take one Exact product that has a photo, and search with the photo.
The photographed product is removed from the results (finding the same photo again is trivial),
so the score is about finding the query's *other* Exact products.
- recall_other_exact@10: share of the other Exact products in the top 10
- exact_in_top10: how many of the top 10 are Exact for that query

Methods:
- clip   : photo -> CLIP image vector -> nearest product photos (SQID vectors). No LLM.
- gemini : photo -> Gemini writes a search query -> bge-m3 text search. Cached in results/image_queries.jsonl.

Run from the repo root: python -m src.amazon.eval_image_search clip   (or gemini)
"""
import json
import os
import statistics
import sys
from pathlib import Path

from PIL import Image

from src import metrics
from src.amazon.load_esci import DATA_DIR, load_examples, load_query_ids

IMAGE_DIR = DATA_DIR / "sqid" / "images"
CACHE = Path("results/image_queries.jsonl")
K = 10


def pick_photos(examples, query_ids) -> list[tuple[int, str, str]]:
    """(query_id, query, product_id): the first Exact product with a downloaded photo."""
    picks = []
    for qid in query_ids:
        group = examples[(examples["query_id"] == qid) & (examples["esci_label"] == "E")]
        for product_id in sorted(group["product_id"]):
            if (IMAGE_DIR / f"{product_id}.jpg").exists():
                picks.append((qid, group["query"].iloc[0], product_id))
                break
    return picks


def clip_searcher():
    from src.amazon.clip_search import clip_search, embed_image, load_product_vectors
    from src.amazon.pipeline import open_index

    collection, _ = open_index()
    ids, vectors = load_product_vectors(collection.get(include=[])["ids"])
    print(f"CLIP vectors for {len(ids)} of {collection.count()} indexed products", flush=True)

    def run(product_id: str) -> tuple[str, list[str]]:
        vector = embed_image(Image.open(IMAGE_DIR / f"{product_id}.jpg"))
        return "", [p for p, _ in clip_search(vector, ids, vectors, K, exclude={product_id})]
    return run


def gemini_searcher():
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    from src.amazon.image_query import describe_image
    from src.amazon.pipeline import open_index, search

    load_dotenv()
    llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"), temperature=0,
                                 google_api_key=os.getenv("GEMINI_API_KEY"))
    collection, embeddings = open_index()
    cached = {}
    if CACHE.exists():
        cached = {r["product_id"]: r["image_query"] for r in map(json.loads, CACHE.read_text().splitlines())}

    def run(product_id: str) -> tuple[str, list[str]]:
        if product_id not in cached:
            cached[product_id] = describe_image((IMAGE_DIR / f"{product_id}.jpg").read_bytes(), llm)
            with CACHE.open("a") as f:
                f.write(json.dumps({"product_id": product_id, "image_query": cached[product_id]}) + "\n")
        hits = [r["product_id"] for r in search(cached[product_id], collection, embeddings, K + 1)]
        return cached[product_id], [p for p in hits if p != product_id][:K]
    return run


def main(method: str) -> None:
    examples = load_examples()
    run = {"clip": clip_searcher, "gemini": gemini_searcher}[method]()
    rows = []
    for qid, query, product_id in pick_photos(examples, load_query_ids()):
        labels = dict(zip(*examples[examples["query_id"] == qid][["product_id", "esci_label"]].values.T))
        other_exact = {p for p, label in labels.items() if label == "E" and p != product_id}
        image_query, ids = run(product_id)
        rows.append({
            "query_id": qid, "text_query": query, "photo_of": product_id, "image_query": image_query,
            "recall_other_exact@10": metrics.recall(ids, other_exact, K) if other_exact else None,
            "exact_in_top10": sum(labels.get(p) == "E" for p in ids), "top10": ids,
        })
    scored = [r for r in rows if r["recall_other_exact@10"] is not None]
    summary = {
        "method": method, "n_photos": len(rows), "n_with_other_exact": len(scored),
        "mean_recall_other_exact@10": statistics.mean(r["recall_other_exact@10"] for r in scored),
        "mean_exact_in_top10": statistics.mean(r["exact_in_top10"] for r in rows),
    }
    Path(f"results/amazon_image_eval_{method}.json").write_text(
        json.dumps({"summary": summary, "queries": rows}, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "clip")

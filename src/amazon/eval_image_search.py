"""Evaluate image search: product photo -> Gemini query -> text search.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet. Not run yet.

For each plain query, take one Exact product that has a photo, and use the photo as the query.
- self_hit@10: the photographed product itself is in the top 10
- recall_exact@10: share of that query's Exact products in the top 10
Gemini answers are cached in results/image_queries.jsonl, so a rerun does not call it again.

Run from the repo root: python -m src.amazon.eval_image_search
"""
import json
import os
import statistics
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from src import metrics
from src.amazon.image_query import describe_image
from src.amazon.load_esci import DATA_DIR, load_examples, load_query_ids
from src.amazon.pipeline import open_index, search

IMAGE_DIR = DATA_DIR / "sqid" / "images"
CACHE = Path("results/image_queries.jsonl")
OUTPUT = Path("results/amazon_image_eval.json")
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


def main() -> None:
    load_dotenv()
    llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"), temperature=0,
                                 google_api_key=os.getenv("GEMINI_API_KEY"))
    examples = load_examples()
    query_ids = load_query_ids()
    collection, embeddings = open_index()
    cached = {}
    if CACHE.exists():
        cached = {r["product_id"]: r["image_query"] for r in map(json.loads, CACHE.read_text().splitlines())}

    rows = []
    for qid, query, product_id in pick_photos(examples, query_ids):
        if product_id not in cached:
            cached[product_id] = describe_image((IMAGE_DIR / f"{product_id}.jpg").read_bytes(), llm)
            with CACHE.open("a") as f:
                f.write(json.dumps({"product_id": product_id, "image_query": cached[product_id]}) + "\n")
        ids = [r["product_id"] for r in search(cached[product_id], collection, embeddings, K)]
        exact = set(examples[(examples["query_id"] == qid) & (examples["esci_label"] == "E")]["product_id"])
        rows.append({
            "query_id": qid, "text_query": query, "photo_of": product_id, "image_query": cached[product_id],
            "self_hit@10": product_id in ids, "recall_exact@10": metrics.recall(ids, exact, K), "top10": ids,
        })
        print(f"{query!r} -> {cached[product_id]!r} self_hit={product_id in ids}", flush=True)

    summary = {
        "n": len(rows),
        "self_hit@10": statistics.mean(r["self_hit@10"] for r in rows),
        "mean_recall_exact@10": statistics.mean(r["recall_exact@10"] for r in rows),
    }
    OUTPUT.write_text(json.dumps({"summary": summary, "queries": rows}, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

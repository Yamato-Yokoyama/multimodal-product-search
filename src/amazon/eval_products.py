"""Index ESCI products and evaluate search on the plain queries. Runs without an LLM.

✍️ Claude wrote this file (2026-11-08, at Yamato's request). Not reviewed yet.
Same settings as ConstraintRAG v0: bge-m3, Chroma (cosine), one document per product, top 10.
Answer generation with Gemini is left for later (see "generation" in the output).

Run from the repo root: python -m src.amazon.eval_products
"""
import json
import os
import statistics
from pathlib import Path

import chromadb
import torch
from langchain_huggingface import HuggingFaceEmbeddings

from src import metrics
from src.amazon.load_esci import load_corpus, load_examples, load_query_ids

CHROMA_DIR = Path("chroma_db_amazon")
COLLECTION_NAME = "amazon_products"
OUTPUT = Path("results/amazon_plain_eval.json")
GAIN = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}
K = 10
BATCH_SIZE = 64


def get_embeddings() -> HuggingFaceEmbeddings:
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    return HuggingFaceEmbeddings(
        model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 16},
    )


def build_product_index(embeddings, query_ids: list[int]):
    """Reuse the persisted index if it exists; otherwise embed the corpus."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    if collection.count() > 0:
        return collection
    corpus = load_corpus(query_ids)
    print(f"corpus {len(corpus)} products", flush=True)
    for start in range(0, len(corpus), BATCH_SIZE):
        batch = corpus.iloc[start : start + BATCH_SIZE]
        documents = batch["document"].tolist()
        collection.add(
            ids=batch["product_id"].tolist(),
            documents=documents,
            embeddings=embeddings.embed_documents(documents),
            metadatas=[{"product_id": p, "title": t} for p, t in zip(batch["product_id"], batch["title"])],
        )
        print(f"indexed {min(start + BATCH_SIZE, len(corpus))}/{len(corpus)}", flush=True)
    return collection


def main() -> None:
    query_ids = load_query_ids()
    examples = load_examples()
    judged = examples[examples["query_id"].isin(query_ids)]
    embeddings = get_embeddings()
    collection = build_product_index(embeddings, query_ids)

    rows = []
    for qid in query_ids:
        group = judged[judged["query_id"] == qid]
        query = group["query"].iloc[0]
        labels = dict(zip(group["product_id"], group["esci_label"]))
        found = collection.query(query_embeddings=[embeddings.embed_query(query)], n_results=K)
        ids = found["ids"][0]
        exact = set(group.loc[group["esci_label"] == "E", "product_id"])
        rows.append({
            "query_id": qid,
            "query": query,
            "ndcg@10": metrics.ndcg([GAIN.get(labels.get(p), 0.0) for p in ids], K, [GAIN[l] for l in group["esci_label"]]),
            "recall_exact@10": metrics.recall(ids, exact, K),
            "exact_in_top10": sum(labels.get(p) == "E" for p in ids),
            "judged_in_top10": sum(p in labels for p in ids),
            "top10": [{"product_id": p, "title": m["title"], "label": labels.get(p)} for p, m in zip(ids, found["metadatas"][0])],
            "generation": None,  # slot for the Gemini answer and its check, filled later
        })

    summary = {
        "n": len(rows),
        "corpus_size": collection.count(),
        "mean_ndcg@10": statistics.mean(r["ndcg@10"] for r in rows),
        "mean_recall_exact@10": statistics.mean(r["recall_exact@10"] for r in rows),
        "mean_exact_in_top10": statistics.mean(r["exact_in_top10"] for r in rows),
        "mean_judged_in_top10": statistics.mean(r["judged_in_top10"] for r in rows),
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps({"summary": summary, "queries": rows}, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

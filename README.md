# Multimodal Product Search

A shopping assistant over Amazon product data (ESCI). Ask in words or attach a product photo.
It started from my first RAG project, LangChain RAG Explorer, and reuses its LangGraph flow
(query rewriting for follow-ups, a critic step, a SQLite checkpointer) with Amazon data only.

Status: trial. Text search is evaluated; the Gemini parts (answers, photo to query) are built but not run yet.

## Flow

```
input ─ router ─┬─ photo     → describe_image (Gemini) ─┐
                ├─ follow-up → contextualize ───────────┤
                └─ text ────────────────────────────────┴→ search → generate → critic → record_history
```

The router looks at the input (photo or not, history or not), not at the meaning of the question.

## Data

- Amazon ESCI (Apache-2.0), US, test split, Task 1 part (`small_version = 1`)
- 50 plain queries without negation words: 20 from ConstraintRAG + 30 random (seed 42), `eval/amazon_plain_queries.json`
- Index: judged products for those queries + 5,000 random products, one document per product (title + description), bge-m3, Chroma
- Photos: image URLs from SQID (MIT; Crossing Minds, [arXiv 2405.15190](https://arxiv.org/abs/2405.15190)). SQID ships URLs and CLIP embeddings, not the photos. The photos are Amazon's and stay local; `scripts/fetch_product_images.py` downloads them again

## Results (2026-11-08)

| Search | n | nDCG@10 | Exact Recall@10 |
|---|---|---|---|
| Text, bge-m3 | 50 queries | 0.551 | 0.547 |
| Photo → Gemini → text | not run yet | | |

Unjudged products count as 0, so nDCG may be lower than the true value.

## Run

```
python scripts/build_plain_queries.py        # query set
python -m src.amazon.eval_products           # index + text evaluation
python scripts/fetch_product_images.py       # photos (slow, 0.5 s each)
python -m src.amazon.eval_image_search       # photo evaluation (Gemini, 15 calls a minute)
chainlit run src/amazon/chainlit_app.py      # chat UI
```

Set `ESCI_DATA_DIR` if the ESCI files are not in `../constraintrag/data`.

## Related

- ConstraintRAG: the follow-up project on negated queries ("without X"), which this assistant does not handle.

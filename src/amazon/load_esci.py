"""Load Amazon ESCI products as one document per product (title + description).

✍️ Claude: copied from ConstraintRAG app/src/load_esci.py (2026-11-08) and changed to read
the plain-query set. Data stays in ConstraintRAG's data folder (set ESCI_DATA_DIR).
"""
import json
import os
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.getenv("ESCI_DATA_DIR", "../constraintrag/data"))
QUERIES_PATH = Path("eval/amazon_plain_queries.json")
HTML_TAG = re.compile(r"<[^>]+>")
MAX_CHARS = 1500


def clean_text(value) -> str:
    if not isinstance(value, str) or value.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", HTML_TAG.sub(" ", value)).strip()


def make_document(title, description) -> str:
    return f"{clean_text(title)}\n{clean_text(description)}".strip()[:MAX_CHARS]


def load_query_ids(path: Path = QUERIES_PATH) -> list[int]:
    return json.loads(path.read_text())["query_ids"]


def load_examples() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "examples_us.parquet")


def load_corpus(query_ids: list[int], extra_products: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Judged products for the eval queries, plus random products from the rest of ESCI."""
    examples = load_examples()
    products = pd.read_parquet(DATA_DIR / "products_us.parquet").drop_duplicates("product_id")
    judged = examples[examples["query_id"].isin(query_ids)]["product_id"].unique()
    is_judged = products["product_id"].isin(judged)
    rest = products[~is_judged]
    sampled = rest.sample(n=min(extra_products, len(rest)), random_state=seed)
    corpus = pd.concat([products[is_judged], sampled]).copy()
    corpus["document"] = [
        make_document(title, description)
        for title, description in zip(corpus["product_title"], corpus["product_description"])
    ]
    corpus["title"] = corpus["product_title"].map(clean_text)
    return corpus[corpus["document"] != ""][["product_id", "title", "document"]]

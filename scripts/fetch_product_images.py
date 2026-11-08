"""Download SQID images for the judged products of the plain queries, at a low rate.

✍️ Claude wrote this file (2026-11-08, at Yamato's request). Not reviewed yet.
Based on ConstraintRAG app/src/vision/fetch_images.py. Images go to ConstraintRAG's
data/sqid/images (shared, kept out of git: redistribution of SQID images is unverified).

Run from the repo root: python scripts/fetch_product_images.py
"""
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.amazon.load_esci import DATA_DIR, load_examples, load_query_ids  # noqa: E402

IMAGE_DIR = DATA_DIR / "sqid" / "images"


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    examples = load_examples()
    wanted = set(examples[examples["query_id"].isin(load_query_ids())]["product_id"])
    tables = [pd.read_parquet(DATA_DIR / "sqid" / name) for name in ("product_image_urls.parquet", "supp_product_image_urls.parquet")]
    rows = pd.concat(tables).dropna(subset=["image_url"]).drop_duplicates("product_id")
    rows = rows[rows["product_id"].isin(wanted)]
    failed = 0
    for product_id, url in zip(rows["product_id"], rows["image_url"]):
        path = IMAGE_DIR / f"{product_id}.jpg"
        if path.exists():
            continue
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "rag-explorer-amazon-research"})
            path.write_bytes(urllib.request.urlopen(request, timeout=20).read())
        except Exception as error:
            failed += 1
            print(f"failed {product_id}: {error}", flush=True)
        time.sleep(0.5)
    print(f"wanted {len(wanted)}, with url {len(rows)}, failed {failed}", flush=True)


if __name__ == "__main__":
    main()

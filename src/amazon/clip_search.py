"""Search products by image with CLIP: a photo (or text) and product photos share one vector space.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.
Product vectors come from SQID (clip-vit-large-patch14 image features, MIT). The same model
embeds the user's photo here, so both sides match.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from src.amazon.load_esci import DATA_DIR

MODEL = "openai/clip-vit-large-patch14"
FEATURES = DATA_DIR / "sqid" / "product_features.parquet"
CACHE = Path("chroma_db_amazon/clip_products.npz")


@lru_cache(maxsize=1)
def _model():
    return CLIPModel.from_pretrained(MODEL).eval(), CLIPProcessor.from_pretrained(MODEL)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


def load_product_vectors(product_ids: list[str]) -> tuple[list[str], np.ndarray]:
    """SQID image vectors for the products in our index. Products without a photo are left out."""
    if CACHE.exists():
        data = np.load(CACHE, allow_pickle=False)
        return data["ids"].tolist(), data["vectors"]
    table = pq.read_table(FEATURES, columns=["product_id", "clip_image_features"],
                          filters=[("product_id", "in", list(product_ids))])
    # Some SQID rows have no vector (no photo, or the download failed). Keep full 768-dim vectors only.
    pairs = [(p, v) for p, v in zip(table.column("product_id").to_pylist(), table.column("clip_image_features").to_pylist())
             if v is not None and len(v) == 768]
    ids = [p for p, _ in pairs]
    vectors = _normalize(np.asarray([v for _, v in pairs], dtype=np.float32))
    CACHE.parent.mkdir(exist_ok=True)
    np.savez(CACHE, ids=np.asarray(ids), vectors=vectors)
    return ids, vectors


def _projected(output) -> np.ndarray:
    """transformers 5 returns an output object; the projected embedding is pooler_output."""
    features = output if torch.is_tensor(output) else output.pooler_output
    return _normalize(features[0].numpy())


def embed_image(image: Image.Image) -> np.ndarray:
    model, processor = _model()
    with torch.no_grad():
        output = model.get_image_features(**processor(images=[image.convert("RGB")], return_tensors="pt"))
    return _projected(output)


def embed_text(text: str) -> np.ndarray:
    model, processor = _model()
    with torch.no_grad():
        output = model.get_text_features(**processor(text=[text], return_tensors="pt", padding=True, truncation=True))
    return _projected(output)


def clip_search(query_vector: np.ndarray, ids: list[str], vectors: np.ndarray, top_k: int = 10,
                exclude: set[str] = frozenset()) -> list[tuple[str, float]]:
    scores = vectors @ query_vector
    order = np.argsort(-scores)
    return [(ids[i], float(scores[i])) for i in order if ids[i] not in exclude][:top_k]

"""Pick plain (non-negated) ESCI queries for the Amazon evaluation.

✍️ Claude wrote this file (2026-11-08, at Yamato's request). Not reviewed yet.

Rules (decided with Yamato on 2026-11-08):
- US, test split (the train split was used to train ConstraintRAG's ML reranker)
- no negation words in the query
- at least 10 judged products and at least 1 Exact
- the 20 plain queries from ConstraintRAG, plus 30 random ones (seed 42)

Run from the repo root: python scripts/build_plain_queries.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.amazon.load_esci import QUERIES_PATH, load_examples  # noqa: E402

CONSTRAINTRAG_QUERIES = Path("../constraintrag/app/eval/queries.json")
NEGATION = re.compile(r"\b(?:without|not|no|non|free|except|exclu\w*|never|nothing|less)\b", re.IGNORECASE)
NEW_QUERIES = 30
SEED = 42


def main() -> None:
    examples = load_examples()
    test = examples[examples["split"] == "test"]
    stats = test.groupby(["query_id", "query"]).agg(
        judged=("esci_label", "size"), exact=("esci_label", lambda labels: (labels == "E").sum())
    ).reset_index()
    eligible = stats[(stats["judged"] >= 10) & (stats["exact"] >= 1) & ~stats["query"].str.contains(NEGATION)]

    reused = json.loads(CONSTRAINTRAG_QUERIES.read_text())["plain"]
    missing = set(reused) - set(eligible["query_id"])
    if missing:
        print(f"note: {len(missing)} ConstraintRAG plain queries do not meet the rules: {sorted(missing)}")
    pool = eligible[~eligible["query_id"].isin(reused)]
    new = pool.sample(n=NEW_QUERIES, random_state=SEED)["query_id"].tolist()

    query_ids = [int(q) for q in reused] + [int(q) for q in new]
    QUERIES_PATH.parent.mkdir(exist_ok=True)
    QUERIES_PATH.write_text(json.dumps({
        "note": "20 plain queries from ConstraintRAG + 30 random ESCI test queries (seed 42)",
        "query_ids": query_ids,
    }, indent=2))
    print(f"eligible {len(eligible)}, wrote {len(query_ids)} queries -> {QUERIES_PATH}")
    print(stats[stats["query_id"].isin(new)][["query", "judged", "exact"]].to_string(index=False))


if __name__ == "__main__":
    main()

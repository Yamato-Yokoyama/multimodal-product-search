"""LangGraph flow for the Amazon shopping assistant.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.
Built from RAG Explorer's graph_router (contextualize, critic, record_history, SQLite checkpointer).

The router looks at the input, not at the meaning of the question:
    image      -> image_search (CLIP: photo vs product photos, no LLM)
    follow-up  -> contextualize -> search (bge-m3)
    text       -> search (bge-m3)
then generate -> critic -> record_history.
Gemini photo-to-text (src/amazon/image_query.py) is kept only as a baseline in the evaluation.
"""
import io
import operator
import sqlite3
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from PIL import Image

from src.amazon.clip_search import clip_search, embed_image, load_product_vectors
from src.amazon.pipeline import generate_answer, search, text_of
from src.query_rewriting import contextualize_query


class ShopState(TypedDict, total=False):
    query: str
    image: bytes | None
    image_mime: str
    resolved_query: str
    route: str
    results: list[dict]
    answer: str
    history: Annotated[list[str], operator.add]


def decide_route(state: ShopState) -> Literal["image", "follow_up", "text"]:
    if state.get("image"):
        return "image"
    if state.get("history"):
        return "follow_up"
    return "text"


def build_shop_graph(collection, embeddings, llm, top_k: int = 10, db_path: str = "checkpoints.sqlite"):
    photo_ids, photo_vectors = load_product_vectors(collection.get(include=[])["ids"])

    def router(state: ShopState) -> dict:
        return {"route": decide_route(state), "resolved_query": state["query"]}

    def image_search(state: ShopState) -> dict:
        vector = embed_image(Image.open(io.BytesIO(state["image"])))
        hits = clip_search(vector, photo_ids, photo_vectors, top_k)
        found = collection.get(ids=[p for p, _ in hits], include=["documents", "metadatas"])
        by_id = {p: (d, m) for p, d, m in zip(found["ids"], found["documents"], found["metadatas"])}
        results = [
            {"rank": rank, "product_id": p, "title": by_id[p][1]["title"], "document": by_id[p][0], "score": round(score, 4)}
            for rank, (p, score) in enumerate(hits, start=1)
        ]
        request = state["query"] or "Products that look like the photo"
        return {"results": results, "resolved_query": request}

    def contextualize(state: ShopState) -> dict:
        return {"resolved_query": contextualize_query(state["resolved_query"], state["history"], llm)}

    def retrieve(state: ShopState) -> dict:
        return {"results": search(state["resolved_query"], collection, embeddings, top_k)}

    def generate(state: ShopState) -> dict:
        return {"answer": generate_answer(state["resolved_query"], state["results"], llm)}

    def critic(state: ShopState) -> dict:
        context = "\n".join(f"[{r['product_id']}] {r['document']}" for r in state["results"])
        response = llm.invoke(
            f"Request: {state['resolved_query']}\nAnswer: {state['answer']}\nEvidence:\n{context}\n\n"
            "If the answer is not supported by the evidence, put '⚠️ Check: ' and the reason first, "
            "then return the answer. Otherwise return the answer unchanged."
        )
        return {"answer": text_of(response)}

    def record_history(state: ShopState) -> dict:
        # The image itself is not kept: the next turn only needs what was searched.
        return {"history": [f"Q: {state['resolved_query']}\nA: {state['answer']}"], "image": None}

    graph = StateGraph(ShopState)
    for name, node in [("router", router), ("image_search", image_search), ("contextualize", contextualize),
                       ("search", retrieve), ("generate", generate), ("critic", critic),
                       ("record_history", record_history)]:
        graph.add_node(name, node)
    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", lambda s: s["route"],
                                {"image": "image_search", "follow_up": "contextualize", "text": "search"})
    graph.add_edge("image_search", "generate")
    graph.add_edge("contextualize", "search")
    graph.add_edge("search", "generate")
    graph.add_edge("generate", "critic")
    graph.add_edge("critic", "record_history")
    graph.add_edge("record_history", END)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(conn))

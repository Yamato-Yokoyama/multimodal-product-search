"""Chainlit UI for the Amazon shopping assistant. Accepts text and product photos.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.
Run from the repo root: chainlit run src/amazon/chainlit_app.py
"""
import os
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

from src.amazon.graph import build_shop_graph  # noqa: E402
from src.amazon.pipeline import open_index  # noqa: E402

# Built once per process: embedding the corpus inside on_chat_start would block every new chat.
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    temperature=0.2,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
collection, embeddings = open_index()
graph = build_shop_graph(collection, embeddings, llm)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Earbuds", message="bose earbuds"),
        cl.Starter(label="Kitchen", message="jumbo cupcake pans"),
        cl.Starter(label="Home", message="olive green throw pillow"),
        cl.Starter(label="Follow-up", message="which of those is the cheapest looking one?"),
    ]


@cl.on_message
async def on_message(msg: cl.Message):
    images = [e for e in msg.elements if (e.mime or "").startswith("image/")]
    state = {"query": msg.content or "", "image": None}
    if images:
        state["image"] = Path(images[0].path).read_bytes()
        state["image_mime"] = images[0].mime
    config = {"configurable": {"thread_id": cl.context.session.id}}
    result = await cl.make_async(graph.invoke)(state, config=config)

    lines = [f"**Route:** {result['route']}　**Searched:** {result['resolved_query']}", "", result["answer"], "", "**Top results**"]
    lines += [f"{r['rank']}. {r['title']} ({r['product_id']}, {r['score']:.3f})" for r in result["results"][:5]]
    await cl.Message(content="\n".join(lines)).send()

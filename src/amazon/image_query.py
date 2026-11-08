"""Turn a product photo into a text query with Gemini (multimodal), so text search can use it.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.
"""
import base64
import time

from langchain_core.messages import HumanMessage

from src.amazon.pipeline import text_of

PROMPT = (
    "This is a photo of a product. Write a short Amazon search query (at most 12 words, English) "
    "that would find this exact product: type of product, brand if visible, color, size or key feature. "
    "Return only the query."
)
# Gemini's free tier allows 15 calls a minute. Keep at least this many seconds between calls.
MIN_INTERVAL = 4.5
_last_call = 0.0


def image_message(image: bytes, mime: str = "image/jpeg", note: str = "") -> HumanMessage:
    data = base64.b64encode(image).decode()
    text = PROMPT + (f"\nThe user also wrote: {note}" if note else "")
    return HumanMessage(content=[
        {"type": "text", "text": text},
        {"type": "image_url", "image_url": f"data:{mime};base64,{data}"},
    ])


def describe_image(image: bytes, llm, mime: str = "image/jpeg", note: str = "") -> str:
    global _last_call
    wait = MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()
    return text_of(llm.invoke([image_message(image, mime, note)]))

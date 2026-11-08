"""
src/chainlit_hello.py

Chainlit の最小 Hello World。
- @cl.on_message デコレータで「メッセージ受信時の処理」を定義
- await cl.Message(...).send() で応答を返す
- ここではまだ LLM を繋げず、単なるエコーで動作確認
"""

import chainlit as cl
import asyncio

@cl.on_message
async def handle_message(message: cl.Message):
    """ユーザーからのメッセージを受けて、エコー返信する。"""

    # 3 秒かかる処理をシミュレート(実際の LLM 呼び出しに近い)
    await asyncio.sleep(3)
    reply = f"3 秒待ちました: {message.content}"
    await cl.Message(content=reply).send()
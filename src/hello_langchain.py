"""
LangChain 版 Hello World。
hello_gemini.py と同じ内容を、LangChain の抽象化を通して呼ぶ。

比較ポイント:
- 生 SDK: client.models.generate_content(model=..., contents=string)
- LangChain: ChatModel.invoke([HumanMessage(...)])
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
# 1. ChatGoogleGenerativeAI は Gemini を LangChain の "ChatModel" として包む。
#    ChatOpenAI や ChatAnthropic と同じインターフェース(.invoke, .stream, .batch)。
#    プロバイダを差し替えるとき、コードの残りは変わらない。ここが LangChain の要。

llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# 2. メッセージは文字列ではなく Message オブジェクトのリスト。
#    - SystemMessage: モデルの役割・振る舞い指定(生 SDK には system_instruction で対応)
#    - HumanMessage: ユーザー発話
#    - AIMessage: モデル応答(履歴を渡すときに使う)
#    構造化されているから、後で会話履歴を扱うときそのまま渡せる。
message = [
    SystemMessage(content="あなたは自己紹介を求められた LLM です。簡潔に答えてください。"),
    HumanMessage(content="日本語で自己紹介してください。あなたが何のモデルか、簡潔に。"),
]


# 3. .invoke() = 同期呼び出し。他に:
#    - .stream() でトークン単位のストリーミング
#    - .batch() で並列呼び出し
#    このメソッド群が全プロバイダで共通、というのが実務でありがたい。
response = llm.invoke(message)

# 4. 返り値は AIMessage オブジェクト。.content で本文、.usage_metadata でトークン数など。
print(response.content)
print(f"\n--- meta ---")
print(f"tokens: {response.usage_metadata}")
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

history = [SystemMessage(content="あなたは Yamato の学習パートナーです。日本語で丁寧に、簡潔に答えてください。")] #メッセージは毎回 invoke で送られるので、Gemini が「毎ターン思い出す」ような効果になる

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
    #     print("\n=== 会話履歴 ===")
    # for msg in history:
    #     role = type(msg).__name__  # HumanMessage / AIMessage / SystemMessage
    #     print(f"[{role}] {msg.text[:100]}")  # 長い応答は 100 文字で切る
        break

    history.append(HumanMessage(content=user_input))
    response = llm.invoke(history)
    history.append(response)

    print(f"Gemini: {response.text}\n")
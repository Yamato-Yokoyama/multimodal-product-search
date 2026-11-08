import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


# 1. .env から環境変数を読み込む
#    → API キーをコードにハードコードしないための基本。
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def make_message(role: str, text: str) -> dict:
    return {"role": role, "parts": [{"text": text}]}

#Main frame
history = []

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        
        import json
        print("Conversation history:")
        print(json.dumps(history, indent=2, ensure_ascii=False)) #ensure_ascii=False を入れないと日本語が \u3042\u3044... になる。indent=2 で見やすく段付き
        break
    
    #1. ユーザー発話を履歴に追加
    history.append(make_message("user", user_input))
    
    #2. 履歴全体をGeminiになげる
    
    response = client.models.generate_content(
        model=model_name,
        contents=history,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
            )
        ),
    )
    
    #3　モデル応答を履歴に追加 
    # history.append(make_message("model", response.text))
    
    answer_text=""
    
    for part in response.candidates[0].content.parts:
        if not part.text:
            continue
        if part.thought:
            print(f"\n[思考] {part.text}")
        else:
            answer_text += part.text

    history.append(make_message("model", answer_text))
    print(f"Gemini: {answer_text}\n")
        
    #Display

    # print(f"Gemini: {response.text}\n")
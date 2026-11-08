import os
from dotenv import load_dotenv
from google import genai


# 1. .env から環境変数を読み込む
#    → API キーをコードにハードコードしないための基本。
load_dotenv()

# 2. Gemini クライアントを初期化
#    Client は Google サーバーへの接続と認証を保持するオブジェクト。
#    以降の呼び出しは全部この client 経由で行う。
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 3. モデル呼び出し
#    - model: どのモデルを使うか(.env で切り替え可能にしておく)
#    - contents: プロンプト本文。文字列 or メッセージのリストを渡せる。
#    - 内部では HTTPS POST /v1beta/models/xxx:generateContent が走っている
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

response = client.models.generate_content(
    model=model_name,
    contents="日本語で自己紹介してください。あなたが何のモデルか、簡潔に。",
)

# 4. レスポンスを表示
#    response は複雑な構造(候補、安全性評価、使用トークン数など)を持つが、
#    本文だけなら .text で取れる。この「便利プロパティ」の存在は覚えておく。
print(response.text)
"""
src/hello_mcp.py

MCPの最小サンプル。hello_gemini.pyで書いた「Geminiを直接呼ぶAPIコード」を、
そのままMCPの「ツール」として公開するとどう変わるかを確認する。

見て理解するための実装なので、hello_gemini.pyと同様フルで書いてある
(TODOスキャフォールドではない、レシート自動化の本実装は別ファイルで
TODOスキャフォールドとして用意する予定)。

背景: docs/notes/mcp-101-tutorial/01_why_and_what.md
Depends on: mcp(既にrequirements.txtに入っている), google-genai, python-dotenv
"""
import os
from dotenv import load_dotenv
from google import genai
from mcp.server.fastmcp import FastMCP

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


# ============================================================
# ここまではhello_gemini.pyと全く同じ発想: Geminiを直接呼ぶだけの関数。
# MCPを使うからといって、Geminiの呼び方自体は何一つ変わらない。
# ============================================================
def _summarize_via_gemini(text: str) -> str:
    """Geminiに文章を渡して、日本語1文の要約を返してもらう。

    これは普通のAPI呼び出し。hello_gemini.pyの`client.models.generate_content(...)`
    と同じもの。ここだけ見るとMCPは一切関係ない。
    """
    response = client.models.generate_content(
        model=model_name,
        contents=f"次の文章を日本語で1文に要約してください:\n\n{text}",
    )
    return response.text


# ============================================================
# ここからが新しい部分。上の関数を「MCPのツール」として公開する。
#
# FastMCP("名前") でサーバーのインスタンスを作り、
# @mcp.tool() を関数につけるだけで、
#   - 関数のdocstring(説明文)
#   - 引数の型ヒント(text: str)
#   - 戻り値の型ヒント(-> str)
# から、「この関数は何をするか」「どんな引数を渡せばいいか」を
# MCPクライアント(Claude Desktop, Claude Codeなど)が自動的に理解できる形
# (JSON Schema)に、ライブラリが勝手に変換してくれる。
#
# これが前回説明した「人間が統合コードを書かなくていい」の正体。
# 普通のAPIなら「このエンドポイントはこういう引数を受け取ります」という説明を
# 人間がドキュメントを読んで、呼び出し側のコードに手で書く必要があるが、
# MCPでは@mcp.tool()をつけた時点でその説明が自動生成され、繋いだ瞬間に
# クライアント側に伝わる。
# ============================================================
mcp = FastMCP("hello-mcp-demo")


@mcp.tool()
def summarize(text: str) -> str:
    """渡された文章を日本語で1文に要約するツール。

    Input:
        text: 要約したい文章

    Output:
        str: 日本語1文の要約

    なぜ:
        MCPクライアントは、この関数を直接importして呼ぶわけではない。
        接続時にこのdocstringと型ヒントを読み取って「summarizeという
        ツールがあり、textという引数(文字列)を渡せば要約が返る」と理解し、
        必要な時に(LLMが判断して)呼び出す。
    """
    return _summarize_via_gemini(text)


if __name__ == "__main__":
    # サーバーを起動する。これ単体を `python src/hello_mcp.py` で実行しても
    # 画面には何も表示されない(MCPクライアントからの接続を待ち受ける状態になるだけ)。
    # 動作確認は、Claude DesktopやClaude Codeの設定ファイルにこのサーバーを
    # 登録してから、実際に「summarizeツールを使ってこの文章を要約して」と
    # 話しかけて確認する(設定方法は02で扱う)。
    mcp.run()

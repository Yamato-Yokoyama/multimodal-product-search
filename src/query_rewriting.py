"""
src/query_rewriting.py

クエリを retrieval に効きやすい形に変換するユーティリティ集。
複数の戦略を並列に並べて、実験で比較する用。

Called by:
    - src/rag_pipeline.py の search() 内で条件付き呼び出し

Depends on:
    - langchain_google_genai (LLM)
"""

from langchain.messages import HumanMessage, SystemMessage

def expand_query_to_definition(query: str, llm) -> str:
    """
    ユーザーの質問を、定義的な平叙文に拡張する。
    Speech Act ミスマッチ(Directive query vs Assertive chunks)への対処。
    
    Input:
        query: ユーザーの元クエリ(例: "Q-principle って何?")
        llm: ChatGoogleGenerativeAI インスタンス
    
    Output:
        str: 拡張されたクエリ(例: "Q-principle の定義。Neo-Gricean...")
    
    なぜ:
        - 素朴 embedding 検索で発見された Speech Act ミスマッチへの構造的対処
        - Directive(質問) → Assertive(定義的平叙文) の翻訳を LLM に任せる
        - retrieval の cosine score が上がる = Q-principle chunk が上位に来る
    """
    
    sytem_prompt ="""
    あなたは検索クエリの拡張を担当します。
    ユーザーの質問を、embedding ベースの検索で関連文書がヒットしやすい形に書き換えてください。

    ルール:
    - 質問文ではなく、定義的な平叙文の形にする
    - 関連する専門用語、同義語、期待される答えの語彙を含める
    - 地名が出てきたら、より広い/別の地域名も候補に含める(例: 日本 → Asia-Pacific, APAC)
    - 役職名が出てきたら、会社によって呼び方が違う類義の役職名も候補に含める
      (例: VP → 統括, ディレクター, 部門責任者, General Manager)
    - 1-2 文で簡潔に
    - 質問に答えるのではなく、拡張だけを返す

    例:
    入力: "光合成って何?"
    出力: "光合成の定義とプロセス。植物が光エネルギーを化学エネルギーに変換する過程で、二酸化炭素と水から糖と酸素を生成する反応。"

    入力: "Docker のメリット?"
    出力: "Docker のメリットと利点。コンテナ化技術による環境の一貫性、デプロイの容易さ、リソース効率の向上。"

    入力: "DeepL Japanの担当者は誰?"
    出力: "DeepL Japan、日本、またはAsia-Pacific(APAC)地域を統括する担当者。役職はVice President、Director、General Manager、または日本語で統括・代表・責任者と呼ばれる立場を含む。"

    入力: "SAPのVPとつながっていますか?"
    出力: "SAPのVice President(VP)、または日本語で統括・部門責任者・ディレクターと呼ばれる役職の人物とのつながり。"
    """
    
    message = [
        SystemMessage(content=sytem_prompt),
        HumanMessage(content=f"入力： {query}\n出力:"),
    ]
    
    response = llm.invoke(message)

    return response.text.strip()


def contextualize_query(query: str, history: list[str], llm) -> str:
    """
    会話履歴を踏まえて、指示語(それぞれ/その人/あの人 等)を含むクエリを
    自己完結した形に書き換える(Issue #21, deixis/指示語の解決)。

    Input:
        query: ユーザーの今回のクエリ(例: "それぞれの役職は?")
        history: これまでの会話の記録。1ターン分が1つの文字列
            (例: ["Q: SAPで最近つながった人を3人教えて\\nA: I.K., M.S., Y.H."])
        llm: ChatGoogleGenerativeAI インスタンス

    Output:
        str: 指示語を解決し、自己完結させたクエリ
            (例: "I.K., M.S., Y.H.それぞれの役職は?")

    なぜ:
        - 開発ログ(2026-08-20)で発見済みの課題: on_message は毎ターン独立で、
          「それぞれ」が何を指すか分からず破綻していた
        - expand_query_to_definition と同じ設計(LLMにルール+few-shot例を与えて
          書き換えさせる)だが、こちらは「retrievalに効きやすくする」のではなく
          「会話履歴を見て指示語を解決する」という別の目的
        - historyが空(1ターン目)の場合は、書き換えずそのまま返してよい
    """
    # TODO 10: expand_query_to_definition と同じパターンで実装する。
    #   ヒント:
    #   - history が空リストなら、LLMを呼ばずそのまま query を return する(1ターン目はそのまま)
    #   - SystemMessage には「これまでの会話を踏まえて、指示語を具体的な内容に
    #     置き換えて書き直してください。指示語が無ければそのまま返してください」
    #     というルール + few-shot例(上のdocstringの例のような)を書く
    #   - HumanMessage には history を文字列として繋げたもの + 今回の query を渡す
    #     (例: f"これまでの会話:\\n{'\\n'.join(history)}\\n\\n今回の質問: {query}")
    #   - llm.invoke([...]) を呼び、.text.strip() を返す
    
    if not history:
        return query
    
    system_prompt = """
    これまでの会話を踏まえて、指示語(それぞれ/その人など)があれば、具体的な内容に置き換えて書き直してください。指示語が無ければそのまま返してください。
    指示語を置き換える際は、人名だけでなく、会話に出てきた会社名などの文脈情報もできる限り残してください(検索の手がかりになる情報を落とさないこと)。
    例:
    入力: これまでの会話: Q: SAPで最近つながった人を3人教えて\nA: I.K., M.S., Y.H.\n今回の質問: それぞれの役職は?
    出力: SAPで最近つながったI.K., M.S., Y.H.それぞれの役職は?
    入力: これまでの会話: Q: 今月スーパーで買った商品の中で、1番高かったもの3つ教えて\nA:牛肉、ワイン、チーズ\n今回の質問: その中で、どれが一番高かった?やその中でそれぞれの品物はどこで買ったのか？
    出力: 牛肉、ワイン、チーズの中で、どれが一番高かったか、またそれぞれの品物はどこで買ったのか？
    """
    
    history_text = "\n".join(history)
    message = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"これまでの会話:\n{history_text}\n\n今回の質問: {query}"),
    ]
    
    response = llm.invoke(message)

    return response.text.strip()

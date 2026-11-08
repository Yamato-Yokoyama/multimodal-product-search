# LangGraph 03: 実際のアプリ(Chainlit)への接続

> 01/02の続き。Issue #29。`docs/notes/langgraph-101-tutorial/`をLangGraphの実装先(Chainlit)に接続した実例として記録する。

---

## 何を変えたか

`chainlit_app.py`の中で、Router呼び出しを1行差し替えただけ。

**Before**:
```python
from src.router import router_answer
...
answer = router_answer(msg.content, collection, df, linkedin_df, llm)
```

**After**:
```python
from src.graph_router import build_router_graph
...
graph = build_router_graph(collection, df, linkedin_df, llm)  # モジュールレベルで1回だけ
...
result = graph.invoke({"query": msg.content, "answer": ""})
answer = result["answer"]
```

## 副次的に減ったもの: `cl.user_session`に保存するキー

**Before**: `llm` / `collection` / `df` / `linkedin_df` の**4つ**をセッションに保存し、`on_message`側で4つとも取り出して`router_answer`に渡していた。

**After**: `graph`の**1つだけ**。理由は、`collection`/`df`/`linkedin_df`/`llm`が`build_router_graph()`の中でクロージャとして捕まえられているため(02で触れた「大きいリソースはStateに入れずクロージャで渡す」設計)。呼び出し側は「グラフに聞く」だけで済むようになった。

## ユーザー体験は変わらない、エンジニアリング的には基盤ができた

Chainlitの画面を触っている分には、何も変わって見えない。同じ質問に同じ答えが返ってくる。**ここが重要な点**: この接続作業自体は、機能追加ではなく**将来の機能追加のための土台**を作る作業だった。

| 観点 | メリット | デメリット/コスト |
|---|---|---|
| ユーザー体験 | 変化なし | 変化なし(=この作業だけでは何も新しく「できる」ようにならない) |
| コード構造 | Router のロジックが、状態と分岐を明示的に持つLangGraphのグラフとして表現された。次にCheckpointerを足す時、State/Nodeの構造は既にできているので**そこに1つ機能を足すだけ**で済む | 素の`if/elif`(旧`router.py`)より、グラフを組み立てる分だけ抽象化の層が1つ増えた |
| デバッグのしやすさ | `graph.get_graph().draw_ascii()`でいつでも構造を可視化できる(旧実装にはこの手段が無かった) | 新しい語彙(State/Node/Edge)を覚える必要がある |
| 次の一手 | Issue #21 stage 2(Checkpointer追加、会話履歴の保存)が、既存の`build_router_graph()`に`checkpointer=`引数を足すだけで着手できる状態になった | まだCheckpointerが無いので、マルチターンの課題(開発ログ 2026-08-20)自体はまだ解決していない |

**エンジニア向けの一言でまとめると**: 「今日、ユーザーに見える機能は何も増えていません。ですが、次に会話履歴を扱う機能を追加する時、Routerを一から作り直す必要がなくなりました」。地味だが、機能追加ではなく**土台を先に作る**という判断ができる、というのは実務でも評価されるポイント。

## 動作確認したこと

- `graph.invoke(...)`をPythonから直接呼び、想定通りの回答が返ることを確認
- `PYTHONPATH=. chainlit run src/chainlit_app.py --headless`で実際にサーバーを起動し、HTTP 200で応答することを確認(ブラウザでの目視確認は別途推奨)

---

## 面接練習用: 1段の言い回し

「LangGraphへの移行を、機能追加とインフラ整備の2段階に分けました。まず今日、Routerのロジックを壊さずにLangGraphのグラフとして配線し直し、Chainlitアプリに接続しました。ユーザーから見た挙動は一切変わっていませんが、次に会話履歴の保存(Checkpointer)を追加する際、既存の構造に1つ引数を足すだけで済む状態を先に作った、という位置づけです。」

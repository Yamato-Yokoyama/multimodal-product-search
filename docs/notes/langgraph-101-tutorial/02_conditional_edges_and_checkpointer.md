# LangGraph 02: 条件分岐edgeとCheckpointer

> `01_hello_world.md`の続き。Issue #21(2ターン会話の指示語解決)に着手する前に押さえる基礎パート2。
> 01の`State`/`Node`/`Edge`/`compile`/`invoke`が分かっている前提。

---

## 条件分岐edge(Conditional Edge)

**Input**: `state`を受け取り、**次に実行するノード名(文字列)を返す関数**
**Output**: グラフが、その返り値のノードに分岐する
**なぜ**: 今の`route()`(if/elifで`semantic`/`aggregation`/`table_display`/`linkedin_table`を判定している部分)を、LangGraphの正式な仕組みとして表現するとこの形になる。ロジック自体(何を判定するか)は変える必要がない

```python
def decide(state: MyState) -> str:
    if state["flag"]:
        return "node_a"
    else:
        return "node_b"

graph_builder.add_conditional_edges(
    "router_node",   # ← このノードの実行が終わった後に判定する
    decide,          # ← state を見て次のノード名を返す関数
    {"node_a": "node_a", "node_b": "node_b"},  # 返り値 → 実際のノード名 の対応表
)
```

`route()`との対応: 今の`route()`が返す`"semantic"`/`"aggregation"`/`"table_display"`/`"linkedin_table"`という文字列が、まさに`decide`関数の返り値に相当する。判定ロジックはそのまま移植できる。

## Checkpointer(会話履歴の保存・復元)

**Input**: `compile()`する時に`checkpointer=`として渡すインスタンス(開発中は`MemorySaver()`、本番ならPostgres等に差し替え可能)
**Output**: 各ノード実行後の状態が自動保存される。同じ`thread_id`で`invoke`すると、前回の状態が引き継がれる
**なぜ**: これが**「それぞれの役職は?」のようなフォローアップ質問に答えるための土台**そのもの。会話ごとに`thread_id`(ChainlitのセッションIDに対応させられる)を分ければ、ユーザーごとに独立した会話履歴が保たれる

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)

# thread_id が「どの会話か」を識別するキー
config = {"configurable": {"thread_id": "conversation-1"}}

graph.invoke({"text": "turn1"}, config=config)
graph.invoke({"text": "turn2"}, config=config)  # ← 同じthread_idなら前のstateに引き続き処理される
```

**実際に動作確認した結果**(このプロジェクトのlanggraph==1.2.10で検証済み):
```
turn1: {'text': 'turn1 [A]', 'flag': True}
turn2: {'text': 'turn2 [B]', 'flag': False}
history length: 8
```
`graph.get_state_history(config)`で、指定した`thread_id`の過去の状態変遷を遡って見ることもできる(デバッグ・「なぜこの回答になったか」の追跡に使える)。

## Issue #21への接続(次にやること)

Issue #21の「それぞれの役職は?」を解けるようにするには、この2つを組み合わせる:

1. `route()`の前に「会話履歴を見て指示語を解決する」ノード(contextualizeノード)を挟む
2. そのノードが参照する会話履歴は、Checkpointerが自動的に保存・復元してくれるstateから読む
3. `thread_id`は、Chainlitの`cl.user_session`(既に開発ログ 2026-08-19 で「per-user Common Ground」と位置づけ済み)のセッションIDと対応させる

---

## 早見表(01の続き)

| やりたいこと | 書き方 |
|---|---|
| 条件分岐する | `graph_builder.add_conditional_edges("元ノード", 判定関数, {返り値: 行き先ノード, ...})` |
| 会話履歴を保存できるようにする | `graph_builder.compile(checkpointer=MemorySaver())` |
| どの会話かを指定して実行 | `graph.invoke({...}, config={"configurable": {"thread_id": "..."}})` |
| 過去の状態変遷を見る | `graph.get_state_history(config)` |

## この教科書の使い方

01と合わせて、State/Node/Edge/条件分岐/Checkpointerの基礎が揃った。次はIssue #21の実装(`route()`をLangGraphの条件分岐edgeとして組み直し、contextualizeノードを追加する)に進む。実装用のTODOスキャフォールドは、着手する時に別途用意する。

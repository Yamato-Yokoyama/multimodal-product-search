# LangGraph 101: Hello World(基礎)

> `docs/notes/langgraph-101-tutorial/`は、LangGraphの基礎〜応用を貯めていく教科書フォルダ。
> `01`が基礎、必要な実装が増えるたびに`02`, `03`...を追加していく(このRAGプロジェクトで実際に使った分だけ増える想定)。
> コードを書く時は、このファイルを見ながら`src/hello_langgraph.py`のTODOや、実際のプロジェクトコードを書き進める。
>
> 「なぜLangGraphが要るか」「業界での使われ方」「言語学との接続」は[00_concepts.md](00_concepts.md)を参照(あちらは概念、こちらは実装リファレンス用、と役割を分けている)。

---

## State

**Input**: なし(型定義そのもの)
**Output**: `TypedDict`を継承したクラス。ノード間を流れるデータの「形」を決める
**なぜ**: 全ノードがこの形に従ってデータを受け渡しするための共通契約

```python
from typing import TypedDict

class MyState(TypedDict):
    text: str
    count: int  # キーはいくつでも足せる
```

## Node(ノード)

**Input**: `state`(その時点の`MyState`)
**Output**: `dict`。**更新したいキーだけ**を返せばいい(state全部を返す必要はない)
**なぜ**: LangGraphが返ってきたdictを自動でstateにマージしてくれる。1関数=1つの仕事、が基本

```python
def my_node(state: MyState) -> dict:
    value = state["text"]        # 1. state から取り出す
    result = value.upper()       # 2. 変換する
    return {"text": result}      # 3. 更新分だけ返す
```

## グラフの組み立て(StateGraph → add_node → set_entry_point → add_edge → compile)

**Input**: Stateの型、登録したいノード関数たち
**Output**: `.invoke()`で実行できるcompile済みグラフ
**なぜ**: ノードを繋いで初めて「グラフ」になる。この5行の型を覚えれば大抵の基本形は組める

```python
from langgraph.graph import StateGraph, END

graph_builder = StateGraph(MyState)          # 1. 器を作る
graph_builder.add_node("step1", my_node)     # 2. ノード登録("名前", 関数)
graph_builder.add_node("step2", another_node)
graph_builder.set_entry_point("step1")       # 3. 開始ノードを指定
graph_builder.add_edge("step1", "step2")     # 4. A→Bの順番を繋ぐ
graph_builder.add_edge("step2", END)         # 5. 最後はENDに繋いで終了を明示
graph = graph_builder.compile()              # 6. 実行可能な形にする
```

## invoke(実行)

**Input**: 初期state(dict、`MyState`の形に合わせる)
**Output**: 全ノードを通過した後の最終state(dict)
**なぜ**: compileしたグラフに実際にデータを流して結果を得る、唯一のエントリーポイント

```python
result = graph.invoke({"text": "hello", "count": 0})
print(result)  # 全ノードを通過した後のstate全体が返る
```

---

## 早見表(困った時にここだけ見る)

| やりたいこと | 書き方 |
|---|---|
| Stateにキーを増やす | `class MyState(TypedDict): 新キー: 型` |
| ノードを追加する | `graph_builder.add_node("名前", 関数)` |
| ノード同士を繋ぐ | `graph_builder.add_edge("前", "後")` |
| 最初のノードを指定 | `graph_builder.set_entry_point("名前")` |
| グラフを終わらせる | `graph_builder.add_edge("最後のノード名", END)` |
| 実行する | `graph.invoke({...})` |

## この教科書の使い方

1. まずこのファイルのコード片を見て、パターンを掴む
2. `src/hello_langgraph.py`の見本(`_add_one`/`_double`)で、実際に動く形を確認する
3. 自分のTODO(文字列版、または実際のRAGプロジェクトのノード)を、同じパターンで書く
4. さらに高度な機能(条件分岐edge、checkpointerによる会話履歴の保存)は[02_conditional_edges_and_checkpointer.md](02_conditional_edges_and_checkpointer.md)にまとめてある
5. 実際のアプリ(Chainlit)への接続例は[03_wiring_into_chainlit.md](03_wiring_into_chainlit.md)
6. Stateを「蓄積」させて会話履歴を持たせる書き方は[04_accumulating_state_for_conversation_history.md](04_accumulating_state_for_conversation_history.md)

# LangGraph 06: Checkpointerの落とし穴(configの正体、compile()忘れ)

> 01〜05の続き。Issue #21 stage 2、TODO13〜14を実際に動かして初めて踏んだ2つのエラーの記録。
> 「compile()にcheckpointerを渡し忘れる」→「渡した瞬間、全呼び出しにthread_idが必須になる」という
> 2段階のハマり方をしたので、同じ轍を踏まないようにまとめておく。

---

## 前提: configの正体(05のロッカーのたとえの再確認)

```python
config = {"configurable": {"thread_id": "test-conversation-1"}}
```

`config`は**ロッカーの番号**でしかない。番号自体には何のデータも入っていない。実データ(`query`/`answer`/`history`)は**checkpointer(`MemorySaver`)側の保管庫**に、この番号をキーにして保存されている。「configがhistoryを運んでいる」わけではなく、「configは“どの番号の保管庫を見るか”を伝えるだけ」というのがポイント([[05_graph_layers_and_turn_loop]]参照)。

---

## ハマった順番

### ① `No checkpointer set`

```python
final_state = graph.get_state(config).values
# ValueError: No checkpointer set
```

**原因**: `build_router_graph()`の最後が`graph_builder.compile()`(引数なし)だった。TODO13のヒント最後の項目「`.compile()`の引数に`checkpointer=MemorySaver()`を渡す」が抜けていた。

`graph.get_state(config)`は「ロッカー室に行って、この番号の中身を見せて」という操作。**ロッカー室(checkpointer)自体が存在しない**ので、番号を渡そうが渡すまいが失敗する。

**直し方**:
```python
return graph_builder.compile(checkpointer=MemorySaver())
```

### ② `Checkpointer requires one or more of the following 'configurable' keys: thread_id, ...`

①を直した直後に発生。**別のノードでの単発テスト呼び出し**(`config`を渡していなかった箇所)が失敗した。

**原因**: checkpointerを付けた瞬間、LangGraphの挙動が変わる。

| 状態 | `invoke()`/`stream()`に`config`は必須か |
|---|---|
| checkpointer**無し** | 不要(その場限りの使い捨て実行、保存も復元もしない) |
| checkpointer**有り** | **常に必須**(どのthread_idの保管庫を使うか指定しないと動けない) |

checkpointerを付ける前に書いた「configなしの単発呼び出し」コードは、checkpointerを付けた後にはそのままでは動かない。**checkpointerを付けたら、その`graph`を呼ぶ全箇所に`config`(thread_id)を通す**必要がある。

**直し方**: 単発テストにも専用の`thread_id`を割り当てる(他のテストのhistoryと混ざらないよう、別名にする)。
```python
result = graph.invoke(
    {"query": "4月の合計支出は?", "answer": "", "history": []},
    config={"configurable": {"thread_id": "stage1-test"}},
)
```

---

## 早見表

| やりたいこと | 書き方 |
|---|---|
| checkpointerを有効にする | `graph_builder.compile(checkpointer=MemorySaver())` |
| そのグラフを呼ぶ(checkpointer有り) | `graph.invoke(input, config={"configurable": {"thread_id": "..."}})`(**省略不可**) |
| 保存済みの最終stateだけを読む(再実行しない) | `graph.get_state(config).values` |
| 実行順(どのノードを通ったか)を見たい | `graph.invoke()`ではなく`graph.stream(input, config=config, stream_mode="updates")`でノードごとの出力を逐次取得([[05_graph_layers_and_turn_loop]]参照) |

## 教訓

`draw_ascii()`もそうだったが、**checkpointerまわりは「静的な配線(グラフ構造)」と「動的な要件(呼び出し時のルール)」が別レイヤーで変わる**、という点を意識すること。`compile()`に何を渡すかで、その後の`invoke()`/`stream()`の呼び方の**ルール自体**が変わる(configが任意→必須になる)。エラーメッセージが「さっき直したはずなのに違うエラーが出た」ように見えても、実際には**1つ前の修正が新しいルールを有効化した結果、別の箇所の未対応が露出しただけ**、というケースがある。

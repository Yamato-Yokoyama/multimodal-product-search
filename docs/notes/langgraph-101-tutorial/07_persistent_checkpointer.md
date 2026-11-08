# LangGraph 07: MemorySaver→SqliteSaver(永続化)

> 02・06の続き。「configはロッカー番号でしかなく、実データはcheckpointer側の保管庫にある」
> という06のたとえをそのまま使う。今回変えるのは**保管庫の場所**だけ。

---

## 変えるのは「保管庫の種類」だけ、ロッカー番号の仕組みは一切変わらない

06で説明した通り、`config = {"configurable": {"thread_id": "..."}}`は「ロッカーの番号」でしかない。`MemorySaver`はこの番号ごとのデータを**プロセスのメモリ上**に保管する保管庫、`SqliteSaver`は同じデータを**ファイル(SQLite DB)**に保管する保管庫。番号(`thread_id`)の仕組み・`config`の渡し方・`invoke()`/`stream()`の呼び方は**一切変わらない**。変わるのは`compile()`に渡すcheckpointerのインスタンスだけ。

```
MemorySaver:  thread_id → (プロセスのRAM上の辞書)  ← プロセスが終わると消える
SqliteSaver:  thread_id → (checkpoints.sqliteというファイル)  ← プロセスを再起動しても残る
```

## なぜ`sqlite3.connect(..., check_same_thread=False)`が要るのか

`SqliteSaver`は素のPythonの`sqlite3`モジュールをそのまま使う薄いラッパー。`sqlite3`はデフォルトで「接続(connection)を作ったスレッドからしかアクセスできない」という安全装置を持っている。ChainlitやLangGraphは非同期処理(async)や複数リクエストを扱うため、同じ接続に別のスレッド/タスクからアクセスする可能性がある。`check_same_thread=False`はこの安全装置を明示的に外す指定(この用途では標準的な使い方)。

## 動作確認の仕方

1. `graph.invoke(...)`を`thread_id="persist-test"`で1回実行する
2. プロセスを完全に終了する(`__main__`を1回終わらせる、または別のPythonプロセスから確認する)
3. もう一度同じ`thread_id="persist-test"`で`graph.get_state(config).values`を呼び、historyが残っているか確認する

06で作った`MemorySaver`版のテストは、この手順の2番目(プロセス終了)をやると必ず失敗する(メモリが消えるため)。`SqliteSaver`版は同じ手順で成功するはず、というのが「永続化された」ことの具体的な確認方法になる。

## `checkpoints.sqlite`はgitに入れない

`chroma_db/`と同じ扱いで`.gitignore`に追加済み。会話履歴が入ったファイルなので、`data/tuebingen/receipts_raw/`と同じ理由(実行時に生成される個人的なデータ)でコミット対象外にした。

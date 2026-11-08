# GitHub Actions 101: ci.ymlはどこに置く/何をする(実装編)

> `01_why_and_what.md`の続き。「なぜ要るか」は分かった前提で、実際に`.github/workflows/ci.yml`を
> 書くとどうなるかを説明する。書き終えたら`src/embedding_quality_test.py`を実際に自動実行する
> ところまでがゴール。

---

## 1. まず誤解を1つ解く: workflowファイルは「テストのコードを持つ」わけじゃない

「テストファイルをどこかに置いて、Actionsの時にそれを参照してね、みたいな感じでいいのかな」という理解は、半分正しくて半分ズレています。

- ズレている部分: `ci.yml`の中に`src/embedding_quality_test.py`のテストロジック(assertなど)を**書き写す必要は無い**
- 正しい部分: `ci.yml`は確かに「既にある`src/embedding_quality_test.py`を参照」します。ただしその「参照」の中身は、**あなたが手元のターミナルで打っているコマンドをそのまま1行書くだけ**です

```bash
# あなたが手元でやっていること
$ pytest src/embedding_quality_test.py -v
```

```yaml
# ci.ymlがGitHub上でやらせること(中身は同じコマンド)
      - run: pytest src/embedding_quality_test.py
```

`ci.yml`の役割は「テストの中身」ではなく、「**いつ(push時)、どんな環境で(まっさらなLinux)、何のコマンドを(このpytestコマンドを)実行するか**」という**手順書**です。テストのロジック自体は今まで通り`src/embedding_quality_test.py`に住み続けます。

## 2. どこに置くべきか: これは選択肢が無い、GitHub側の固定ルール

「自分のローカルなファイルに置いて」という発想には、実は**自由度が無い**ことを先に伝えておきます。GitHubは以下のパスを機械的にスキャンして、そこにあるYAMLファイルだけをworkflowとして認識します:

```
.github/workflows/*.yml
```

- このディレクトリ以外にYAMLを置いても、GitHubは一切見つけてくれません(=何も起きない)
- ファイル名自体(`ci.yml`という名前)は慣習であって自由(`test.yml`でも`main.yml`でも動く)。固定なのは**ディレクトリのパスだけ**
- 1つのリポジトリに複数ファイル置ける(将来`lint.yml`, `deploy.yml`と分けることもできる。今回は1ファイルにまとめる)

## 3. pushしてから何が起きるか、時系列

```
1. あなたが `git push` する
2. GitHubが .github/workflows/ci.yml を検知し、on: に書かれた条件(push, pull_request)と一致するか確認
3. 一致したら、GitHubが使い捨てのLinux仮想マシン(runner)を1台用意する
4. runner上で steps を上から順に実行:
   a. actions/checkout でリポジトリのコードをrunnerにコピー
   b. actions/setup-python でPython 3.11を用意
   c. pip install -r requirements.txt で依存を入れる
   d. pytest src/embedding_quality_test.py を実行 ← ここで初めて、あなたの書いたテストが動く
5. 終了コードが0(全テストpass)なら✅、1個でもfailなら❌
6. 結果がPRやcommitの画面に反映される
```

「テストが実際に実行される場所」は5つの手順のうち最後のd番だけで、それ以外(a〜c)は全部「dを実行するための下準備」です。

## 4. 運用の仕方: 今回はこれだけ、今後どう育てるか

今回スコープに入れるのは`src/embedding_quality_test.py`のpytest実行だけです。前回の計画で挙げていたlint(ruff)とdependency audit(pip-audit)は、**まだ`requirements.txt`に入っていない**ので今回は書きません(入っていないツールをCIで呼んでも「コマンドが見つからない」で落ちるだけなので)。

今後増やす時の運用は2パターンあります:

- **同じjobにstepを追記する**(お勧め、今回はこっち): `ci.yml`の`steps:`の下に`- run: ruff check src/`のような行を1行足すだけ
- **別のjobとして並べる**: `jobs:`の下に`lint:`という新しいjobブロックを追加する(pytestが失敗してもlintの結果は別に見える、というメリットがあるが、今回の規模ではオーバースペック)

なので今回作る`ci.yml`には、将来ruffとpip-audit用の場所をコメントで残しておきます。それらを`pip install`したタイミングで、コメントを外して1行ずつ足していく、という育て方をします。

## 5. 1点だけ注意: BGE-M3のロードが重い

さっき実際に`pytest`を手元で回した時、BGE-M3のロードだけで20秒前後かかっていました。CI環境(毎回まっさらな仮想マシン)だと、モデルのダウンロードも毎回発生するのでもっと時間がかかります。今回はまず「動くこと」を優先して、遅さの改善(モデルのキャッシュなど)は後回しにします。

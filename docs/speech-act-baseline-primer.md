# Speech Act分類 Baseline: 予習ノート

> Issue #39の実装に入る前に読む用。「全部Claude任せ」にならないための、
> 言語学的知見・機械学習の基礎・やることの3点セット。
> 実験ログ(実際にやった結果)は`docs/experiments.md`側に書く。こちらは
> 事前知識と計画の置き場。

---

## 1. なぜこれをやるか

キャリアポジショニングの「引き出し2: Speech Actを使ったエージェント意図分類」の
最初の実装ステップ。DailyDialogで学習したSpeech Act分類器は、将来的に
「ユーザ発話をSpeech Act(依頼/質問/情報提供/承諾拒否)で分類してからエージェントの
挙動を決める」という設計の土台になる(今回はそこまで繋がない、分類器単体まで)。

Issue #22で作った`needs_context()`(指示語の有無をLLMに判定させる)と技術的には
似た問題設定(クエリ/発話を見て分類する)だが、こちらは**外部の対話コーパスで
汎用的なパターンを学習**する点が違う(Issue #37はこのプロジェクト固有のクエリで
学習する話、混同しないこと)。

## 2. 言語学的知見: Speech Act理論とDailyDialogのズレ

### Austin/Searleの本来の5分類

- **Assertive**: 何かが真であると主張する(例: 「今日は晴れだ」)
- **Directive**: 相手に何かをさせようとする(例: 「窓を閉めて」「〜してくれる?」)
- **Commissive**: 話者が将来の行為にコミットする(例: 「明日までにやります」)
- **Expressive**: 心理状態を表出する(例: 「ありがとう」「残念だ」)
- **Declarative**: 発話行為そのものが事態を変える(例: 「これを開会とします」)

### DailyDialogの4クラス(簡略版)

| DailyDialogラベル | Searleの対応 | 備考 |
|---|---|---|
| inform | Assertive | 情報提供の陳述 |
| question | Assertiveの下位区分(Searleの5分類には独立クラスが無い) | 情報を求める発話。DailyDialogではinformと別立て |
| directive | Directive | 依頼・指示・提案・申し出への諾否まで含む(Searleより広め) |
| commissive | Commissive | 申し出・提案への承諾/拒否 |
| (無し) | Expressive, Declarative | **DailyDialogには存在しない** |

**押さえておくべきズレ**: DailyDialogは実務データセットとしての簡略版で、
Searleの理論をそのまま実装したものではない。Expressive/Declarativeが欠けている、
questionをAssertiveから独立させている、という2点は面接等で聞かれたら
正直に説明できるようにしておく(理論と実装のギャップを自覚している、という
姿勢自体が評価ポイントになる)。

## 3. 機械学習の基礎(教科書的にざっと)

### TF-IDF

単語の出現頻度(TF)と、その単語がコーパス全体でどれだけ珍しいか(IDF)を掛け合わせた
重み付け。「the」のようなどこにでも出る単語は重みが下がり、そのクラスに特徴的な単語の
重みが上がる。テキストを固定長の数値ベクトルに変換する、最も古典的で今でも通用する手法。

### Naive Bayes(MultinomialNB)

「各単語の出現が(クラスが分かっているという条件下で)互いに独立」という単純化した
仮定(naive)を置いた上でベイズの定理を適用する分類器。この仮定は文法的には明らかに
間違っている(単語は文脈に依存する)が、テキスト分類では驚くほど強いベースラインになる。
理由: 高次元・疎(sparse)な特徴量(TF-IDFベクトル)に対して、少ないデータでも
安定して学習できるため。

### Logistic Regression

Compoundプロジェクトで既にやった手法と同じ。TF-IDFベクトルを入力として、
各クラスに属する確率をロジスティック関数で出す。Naive Bayesと違って
特徴量間の独立性を仮定しないので、単語の組み合わせ(n-gram)が効いてくる場合は
こちらが有利になりやすい。

### なぜ2つ両方やるか

「単純な仮定のモデル(NB)」と「仮定が緩いモデル(LR)」を並べて比較することで、
このタスクにおいて「単語の独立性を仮定しても十分か、それとも単語間の関係を
見た方が良いか」が分かる。これ自体が`docs/experiments.md`に書くべき考察になる。

## 4. 評価指標の基礎

### Precision / Recall / F1(クラスごと)

- Precision: そのクラスと予測した中で実際に正しかった割合
- Recall: 実際にそのクラスだった中で正しく拾えた割合
- F1: PrecisionとRecallの調和平均

### Macro F1(今回の主指標)

各クラスのF1を計算してから、**クラスごとの出現数に関係なく単純平均**したもの。
少数クラス(仮にcommissiveが少なければそれ)の性能低下がそのまま平均に反映されるので、
「多数クラスだけ当てて全体の数字を良く見せる」ことができない、多クラス分類での
標準的な評価軸。

### Confusion Matrix

縦軸=正解ラベル、横軸=予測ラベルの表。対角線が正解、それ以外がどのクラスと
どのクラスを混同しているかを示す。「なぜその混同が起きるか」を言語学的な視点
(例: directiveとcommissiveは会話の中で隣接しやすく、表層的な語彙が似ている)
で説明できると、単なる数字の報告で終わらない考察になる。

## 5. 実務上の注意点

HuggingFaceの`daily_dialog`データセットは名前空間が移動しており、
`datasets.load_dataset("daily_dialog")`は失敗する可能性が高い。
まず`datasets.load_dataset("li2017dailydialog/daily_dialog")`を試すこと。
それでも失敗する場合にMRDAへの切り替えを検討する(Issue #39のブリーフ通り)。

DailyDialogのラベルは4クラス(`__dummy__`を除く: inform/question/directive/
commissive)で、感情ラベルと違い比較的バランスが取れている。全体13,118対話、
train 11,118 / val 1,000 / test 1,000。

## 6. 明日やること(Issue #39のステップ、要約)

1. 依存追加: `scikit-learn`, `datasets`, `pandas`, `matplotlib`, `seaborn`, `jupyter`
2. `notebooks/01_speech_act_baseline.ipynb`でデータロード・探索(ラベル分布、発話長、サンプル確認)
3. `src/ml/train_speech_act.py`: Naive Bayes版(TF-IDF + MultinomialNB)
4. 同ファイルにLogistic Regression版(TF-IDF + LogisticRegression, class_weight="balanced")
5. `src/ml/inference.py`: `SpeechActClassifier`(predict / predict_proba)
6. 評価: 両モデルをtest setでmacro F1・per-class F1・confusion matrixで比較、`docs/experiments.md`に記録
7. コミットをステップごとに分割(Issue #39ブリーフのCommit粒度に従う)

詳細な受け入れ条件(Success Criteria)・Non-goalsはIssue #39本体を参照。
このファイルは「なぜ・何を知っておくべきか」、Issue #39は「何をいつまでに
作るか」という役割分担。

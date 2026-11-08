# Experiments Log

## 2026-09-20 Speech Act Classification Baseline (Issue #39)

### Dataset

- `li2017dailydialog/daily_dialog`(HF Hub、`revision="refs/convert/parquet"`で読み込み。
  通常の`load_dataset("daily_dialog")`は"Dataset scripts are no longer supported"で
  失敗するため、parquetに変換済みのrevisionを明示的に指定する必要があった)
- 発話単位にflatten後: train=87,170 / validation=8,069 / test=7,740
- クラス(train内訳): inform=39,873(45.7%) / question=24,974(28.7%) /
  directive=14,242(16.3%) / commissive=8,081(9.3%)
  → 最多(inform)と最少(commissive)で約5倍の偏り。「比較的バランスが取れている」
  という一部文献の記述は感情ラベルとの相対比較であり、絶対値としては軽視できない
  偏りがある。

### Baseline 1: Naive Bayes (TF-IDF, ngram_range=(1,2), min_df=2)

- Macro F1: **0.539**
- Per-class F1: commissive=0.064, directive=0.502, inform=0.779, question=0.811
- Notes: commissiveのrecallが0.033(718件中ほぼ全て別クラスに誤分類)。
  クラス不均衡への補正機構を持たないため、最少数クラスがinform/questionに
  ほぼ吸収されている。

### Baseline 2: Logistic Regression (TF-IDF, ngram_range=(1,2), min_df=2, class_weight="balanced")

- Macro F1: **0.700**
- Per-class F1: commissive=0.493, directive=0.666, inform=0.780, question=0.862
- Notes: `class_weight="balanced"`によりcommissiveのrecallが0.607まで改善。
  ただしprecisionは0.416まで下がり、「見逃しが減る代わりに誤検出が増える」
  トレードオフが明確に出た。

### Observations

- Logistic RegressionがNaive Bayesをmacro F1で大きく上回った(0.700 vs 0.539)。
  クラス不均衡の扱い(`class_weight="balanced"`)の有無が最大の差だと考えられる
  (NB側にも事前確率の調整は理論上可能だが、今回はデフォルト設定で比較した)。
- 両モデルとも**directiveとcommissiveの混同**が目立つ(confusion matrix参照、
  `notebooks/01_speech_act_baseline.ipynb`)。例: "I will send the report by
  tomorrow."(commissive)をLR版に推論させると directive が最尤(0.458)、
  commissive は 0.187 に留まった。TF-IDFのbag-of-words表現は語順・主語を
  落とすため、「〜します」(commissive、話者が引き受ける)と「〜してください」
  (directive、相手に頼む)のように**話者の役割が違うだけで表層語彙が近い**
  発話ペアを区別しづらいと考えられる。
- DailyDialogの4クラスはSearleの5分類(assertive/directive/commissive/
  expressive/declarative)の簡略版で、expressive/declarativeが存在しない、
  questionがassertiveから独立している、という理論とのズレがある
  (`docs/speech-act-baseline-primer.md` §2 参照)。

### Next

- Issue #39のNon-goalsとして、Transformer/HuggingFaceのfine-tuneとagent/router
  への統合は今回やらない。将来やる場合、上記の「directive/commissive混同」が
  文脈(語順・主語)を見るモデルでどこまで改善するかが焦点になりそう。

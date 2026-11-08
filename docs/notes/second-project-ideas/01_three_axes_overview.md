# キャリア形成の3本の軸(2026-10-01時点)

> 「RAGに飽きた、新しい風が欲しい」という2026-09-30〜10-01の議論から整理。
> JASSO返済という背骨(daily/の別メモ参照)を踏まえ、
> 「どれも自己満にせず、外部評価のある場で検証する」ことを条件にしている。

---

## 3本の軸

| # | 軸 | 位置づけ | 頻度 |
|---|---|---|---|
| 1 | **RAG**(langchain-rag-explorer) | 本線。評価指標の追加(Issue #42)で完成させる | メイン |
| 2 | **ML・新しい分野**(言語学からあえて離れる) | 本線。漫画/音声、どちらも言語学の深い専門知識(文法・音韻論)を要求しない範囲に絞る | メイン |
| 3 | **CL × OSS**([01_categories_and_examples.md](../cl-oss-101-tutorial/01_categories_and_examples.md)参照) | 息抜き・たまに拾う。見つけたら対応する、常に進行中にはしない | 時々 |

---

## 軸2の候補(ML・新しい分野)

### 漫画系(言語に戻らない、純粋に画像だけの選択肢)

CVPR 2025・Manga109-v2026など、現役の研究分野であることを確認済み。

| 案 | 内容 | 使うデータ |
|---|---|---|
| セグメンテーション | コマ・吹き出し・キャラクターの顔/体を検出 | Manga109 + MangaSeg annotations |
| キャラクター再識別 | 絵柄が変わっても同一キャラクターと判定 | Manga109 |
| 読み順推定 | 複雑なコマ割りの正しい読む順番を予測 | Manga109 |
| 話者紐付け | セリフがどのキャラクターのものかを特定 | Manga109Dialog(132,692ペア) |

**要確認**: Manga109は商業漫画が元になっているため、学術利用のライセンス申請が必要。着手前に確認すること。

### 音声系(音韻論を避けた2つの筋)

過去にフーリエ変換で挫折した経験があるため、**信号処理の数式を自分で導出する必要がない**、
既存の音声埋め込みモデル(Wav2Vec2等)を特徴抽出器として使う前提で進める。

| 案 | 内容 | 現役性 | ドイツ求人との繋がり |
|---|---|---|---|
| **ASVspoof 5** | 音声が本物かAI合成(ディープフェイク)かを判定 | 2026年も開催中、1000人以上の話者データ | Voice AI/セキュリティ系求人に直結 |
| **オーディオブック話者紐付け** | 音声クリップがどのキャラクターの声かを特定(漫画の話者紐付けと同じ骨格を音声で解く) | 確立された分野(speaker diarization)の応用 | コールセンター分析・会議の自動議事録・音声認証にも転用可 |

**ドイツの実在求人(確認済み)**:
- Neura Robotics(Metzingen、Tübingenから近い): Audio AIエンジニア、ASR/TTS/VAD
- ai-coustics(ベルリン): Voice AI
- Huawei Research Center Germany: Audio ML

### 音声対話システム系(2026-10-01〜 深掘り中、現時点の最有力候補)

「対話システム」路線(Siri/Alexa/車載音声アシスタント寄り)は、[voice-dialogue-systems-101-tutorial/](../voice-dialogue-systems-101-tutorial/01_pipeline_vs_end_to_end.md)で別途詳しく整理している。

- パイプライン型(ASR→NLU→API→TTS)は実質「軸1(RAG)に音声の皮をかぶせただけ」になりがちで新規性が薄い
- フルデュプレックス型(Moshi等、音声トークンをストリーム処理する方式)は対話の中核設計そのものが別物で、新規性がある
- Tesla Cybercab(2026-09-03ローンチ、Grok統合)、BMW/Mercedes等の「音声ファースト」車載AI投資を確認済み(詳細は[03_industry_findings_in_vehicle_voice.md](../voice-dialogue-systems-101-tutorial/03_industry_findings_in_vehicle_voice.md))
- 課題タイプ別のML汎用性整理(画像/動画への転用可能性)は[02_task_types_and_ml_transfer.md](../voice-dialogue-systems-101-tutorial/02_task_types_and_ml_transfer.md)

---

## Issue化したもの

- [#48](https://github.com/Yamato-Yokoyama/langchain-rag-explorer/issues/48): Speech Act分類のニューラルfine-tune拡張
- [#49](https://github.com/Yamato-Yokoyama/langchain-rag-explorer/issues/49): レシート画像の自前分類器

(漫画・音声系はまだissue化していない、データのライセンス確認等が先)

## 次に確認すべきこと

- [ ] Manga109のライセンス条件(学術利用申請の要否・期間)
- [ ] ASVspoof 5のデータアクセス方法(参加登録が必要か)
- [ ] 上記が難しければ、オーディオブック話者紐付けを軽量に試せる公開データがあるか

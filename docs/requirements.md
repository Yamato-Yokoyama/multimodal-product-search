# 要件定義: LangChain RAG Explorer

> Yamato Yokoyama / 2026年8月 / 更新可能な living ドキュメント
> 次のチャットセッションで詳細化しながら埋めていく形式

---

## 1. User Persona(確定)

### Primary Persona
「日本語話者で、計算言語学や海外キャリアに興味・関心がある学習者」

このペルソナは時間軸で3つの側面を持つが、根っこは同じ人物像:

- **過去の自分**: 高校生時代の Yamato。留学に興味はあるが情報が散らばっていて、何から始めていいか分からない
- **現在の自分**: Tübingen で就活準備中の Yamato。自己客観視、キャリア選択、多言語ドキュメント整理が必要
- **未来のユーザー**: 過去の自分と同じ位置にいる日本の高校生・学部生

### Non-goals
- ドイツ語ネイティブは主対象ではない(Phase 2 で対応検討)
- 中国語・その他言語話者は Phase 3+

## 2. Use Cases(次チャットで詳細化)

### 自問される想定質問カテゴリ

- **About Yamato**: 「Yamato の専門は?」「どんなプロジェクトをやってきた?」「なぜ Tübingen?」
- **About Computational Linguistics**: 「計算言語学って何をする分野?」「NLP との違いは?」「就職先は?」
- **About Studying Abroad**: 「ドイツ大学の学部入学ってどう準備した?」「生活費はどれくらい?」「言語要件は?」
- **About Tübingen**: 「街の雰囲気は?」「大学の特徴は?」「学生生活は?」
- **About LinkedIn Strategy**: 「学生の LinkedIn 活用のコツは?」「アンバサダー経験で何を学んだ?」

### 対応言語(初期)
- 質問言語: 日本語 / 英語
- 応答言語: 質問と同じ言語で返す
- ドキュメント言語: 日本語 / 英語混在で持つ、内部で cross-lingual retrieval

## 3. Data Sources(コーパス構成)

### サブフォルダ構造

```
data/
├── class-notes/          # 授業内容の Markdown ノート(Claude 対話ベース + 自己注釈)
├── linkedin-posts/       # 過去 2-3 年の LinkedIn 投稿(60+ posts, CSV から抽出)
├── tuebingen/            # 街・大学・生活情報
└── self/                 # 自己紹介・CV・キャリア観・生活費など
```

### 各フォルダの想定内容

- **class-notes/**: Semantics & Pragmatics, Text Technology, Phonetics, NLP1/2, Statistics — 授業ごとに Markdown 1つ、自分の言葉でまとめ直したもの
- **linkedin-posts/**: 投稿 CSV から本文を抽出、日付・トピック・言語のメタデータを付与
- **tuebingen/**: 街の情報、大学の紹介、学生生活のリアル
- **self/**: 履歴書(英語)、自己紹介(日/英)、キャリア観、月次生活費、留学準備の振り返り

### 著作権上の扱い

- 授業スライドをそのまま置くのは避ける
- 自分の言葉で書き直したノートは、自分の著作物として扱う
- 授業ノートが Claude との対話ベースであることは README で明示

## 4. Tech Stack(確定、なぜこの選択か)

| Layer | 選択 | 理由 |
|---|---|---|
| **LLM Orchestration** | LangChain | LLM アプリで最大のエコシステム、詰まった時の情報量が桁違い |
| **Stateful Workflow** | LangGraph | セッション管理・分岐フローの必要性が Week 3 で出てくる |
| **Chat UI** | Chainlit | Python 完結でチャット UI が作れる、Ece さんと同じスタック |
| **LLM (dev)** | Ollama (local) or Gemini API Flash 無料枠 | 開発中コストゼロを維持 |
| **LLM (production)** | Gemini API Flash | 学生プランとの親和性、無料枠が広い |
| **Embeddings** | BGE-M3 (via sentence-transformers, local) | 多言語対応、ローカル実行で無料無制限 |
| **Vector DB** | ChromaDB (Week 1-2) → pgvector (Week 3+) | 開発初期は単一ファイル、後で Postgres 統合 |
| **RDB** | PostgreSQL | セッション・履歴・メタデータの永続化、Ece スタックと合わせる |
| **ORM** | SQLAlchemy | Python から DB 操作の業界標準 |
| **Migration** | Alembic | スキーマ変更履歴の管理 |
| **CI/CD** | GitHub Actions (Week 3+) | 自動テスト、ドキュメント生成 |

### 代替候補(面接で聞かれた時のため)

- LLM Orchestration の代替: LlamaIndex (RAG 特化), DSPy (プロンプト最適化), raw code
- Stateful Workflow の代替: CrewAI, AutoGen, LangChain LCEL 単独
- Chat UI の代替: Streamlit, Gradio, Next.js
- Vector DB の代替: Qdrant, Weaviate, FAISS
- Embeddings の代替: OpenAI, Cohere, Voyage AI

## 5. コスト目標

- **開発期間中**: ¥0(全て無料枠/ローカル)
- **応募後・公開時**: 月 ¥1,000 以内を目標(Gemini Flash 無料枠 + 万一の課金)
- **将来サービス化**: BYOK モデル or 無料枠 + プレミアム機能

## 6. Scope

### IN(絶対にやる)
- チャット型 UI で複数言語のドキュメントから回答
- ソース引用付き応答
- セッション履歴の永続化
- 会話履歴の階層型管理(直近詳細、中期要約、遠期ベクトル DB 化)
- 多言語検索(日本語クエリ → 英語ドキュメントヒット等)
- 語用論理論と実装のマッピングを README で言語化

### OUT(絶対にやらない、今回)
- 動画・音声生成
- リアルタイム翻訳
- 外部エージェントアクション(メール送信、カレンダー操作等)
- ユーザー認証(初期はローカル単一ユーザー、Week 3-4 で SSO 検討)
- 本番デプロイ(公開は README + GitHub のみ、実行はローカルで OK)
- 大規模スケーリング

### MAYBE(余裕があれば)
- Deep Agent 実験(Ece さんのプロファイルにあり、時間があれば触る)
- 音声入力(Chainlit にオプションあり)
- Fine-tuning(モデル選択の議論のため触る程度)

## 7. Success Metrics(次チャットで詳細化)

### 技術的成功指標
- 動くデモが 8/12 までに存在する
- 4週間終了時点で GitHub リポジトリに 30+ コミット、日本語コメント付き
- Retrieval 精度: 自作 10 質問セットで Top-3 に正解が含まれる率 > 70%(暫定)
- レスポンス時間: ローカル環境で応答開始まで 3 秒以内

### キャリア的成功指標
- 9/1 に SAP working student ポジションへ応募
- ポートフォリオ URL を含む CV が完成
- 技術ブログ 3-4 本が LinkedIn で発信済み
- 理論マッピングドキュメントが完成

## 8. これから決めること(次チャットで議論)

- [ ] Use Cases の詳細化(想定される質問リスト 20-30 個)
- [ ] 評価用の質問セット 10 個の作成
- [ ] LinkedIn CSV の具体的な処理フロー
- [ ] Chainlit UI の細かい仕様
- [ ] pgvector 移行のタイミング
- [ ] LangChain course の受講計画(DeepLearning.AI 2本 + LangGraph Academy)
- [ ] LLM Challenges research 3本のトピック確定

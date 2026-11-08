---
type: learning-note
date: 2026-08-10
topic: [rag, langchain, embeddings]
status: living-doc
---
ロードスプリット、エンベドレトリープこれらの流れわエンジニアサイドとは全てラングチェインにお願いする感じですか？
自分のイメージだとドキュメントオブジェクトでコンテンツとメタデータで分かれてるって書いてあるけど、辞書型みたいな感じでそれぞれのキーとバリューでバリの中にいっぱい引っ張って、インデックスで指定できるみたいな感じなのかなぁそれが別れていけ。そのままわかるけど、どうしてエンベディングする必要があるのかどうしてそれを省略できないのかって言うこのラグの裏側とラングチェインがどう関わってくるかのオーバー自由を抑えてから行きたい。

いい問い、実装前に整理しておく価値のある話です。順に。

## 誰が何をやるか — 3 層構造

RAG の 4 ステップは、実は **3 層の責任分担**になっています:

- **LangChain の担当**: 部品同士を繋ぐ共通インターフェース、既存ツールのラッパー
- **モデル/DB の担当**: 実際の重い処理(埋め込み計算、ベクトル保存、生成)
- **エンジニア(Yamato)の担当**: **戦略の選択** — どう分割するか、どのモデルを使うか、どう検索するか

LangChain は「オーケストレーター」であって、ML 計算そのものはやってない。Day 1-2 で見た「ChatModel はプロバイダ差し替えだけで動く」の構造が、Loader / Embedding / VectorStore にも同じように適用されている、と思うとスッキリするはず。

## Document オブジェクトの正確な形

Yamato の直感は近いけど、精密にはこう:

```python
Document(
    page_content="Q-principle: 「言えるだけ言え」…",  # テキスト本文(文字列)
    metadata={                                          # フラットな dict
        "source": "data/class-notes/neo-gricean-implicature.md",
        "header_1": "Neo-Gricean Implicature",
        "header_2": "Q-principle(hearer 志向)",
        "confidence": "mixed",
        "date": "2026-06-15",
    }
)
```

「辞書の中に辞書がいっぱい」というより、**「テキスト 1 本 + フラットな metadata 辞書」の 2 属性構造**。ネストはあまり深くならない。

アクセスも `doc[0]` みたいなインデックスじゃなくて、`doc.page_content` と `doc.metadata["header_1"]` みたいに**属性/キー**で取る。

1 ファイル → Load 直後は 1 Document、Split すると多数の Document(各 chunk が 1 Document)。metadata は分割時に継承される + chunk 固有の情報(どのセクションから来たか等)が足される。

## 「なぜ embed するのか」— これが今日の核心

ナイーブな代替を考えると答えが見える。**もし embedding を使わないなら、キーワード検索**になる:

```
質問: "Q-principle って何?"
処理: 全ドキュメントを走査 → "Q-principle" 文字列を含むものを探す → 返す
```

一見動く。でも Yamato のプロジェクトでは **4 つの理由で壊れる**:

**1. 同義語で切れる**
「Q 原則って?」と聞いたら、ノートには「Q-principle」としか書いていない → **1 文字も一致せずヒットしない**。「情報過多」「言えるだけ言え」も同じ概念なのに繋がらない。

**2. 日英クロスで完全に切れる**
日本語質問 → 英語ノート、または逆 → **文字列一致では絶対にヒットしない**。これが Yamato のプロジェクトの最重要要件(REQUIREMENTS.md の「多言語検索」)を直接壊す。

**3. 言い換え質問で切れる**
「Horn が最初に提案した 2 分割は?」→ Q-principle と R-principle の説明を返してほしいのに、質問文にその 2 語がないので探しようがない。

**4. 意味的な関連が拾えない**
「LLM の hallucination と含意理論の関係」→ ネオグライスノートの Yamato メモ(I-principle と hallucination の関係)を返してほしい、が文字列レベルでは繋がらない。

### Embedding が何をやっているか

BGE-M3 のような多言語埋め込みモデルは、テキストを **768〜1024 次元のベクトル**に変換する。この空間で:

- **意味が近い文は、言語や語彙が違ってもベクトルが近い**
- 「Q-principle」「Q 原則」「言えるだけ言え」「Q-heuristic」が同じ領域に集まる
- 「日本語の Q 原則説明」と「英語の Q-principle explanation」も同じ領域に集まる

検索の実体は「質問文をベクトル化 → 空間内で近いドキュメントを探す」= **cosine similarity 計算**。完全に数学の話に還元される。**キーワードの一致は不要**になる。

### 省略できる場合はあるか

Yes、条件付き。参考までに:

- **コーパスが極小**: 全部を context window に直接入れられる場合 → embedding 不要、LLM に丸投げ
- **完全一致検索で足りる**: 名前検索、ID 検索、SKU 検索 → BM25 か SQL LIKE で十分
- **実務のハイブリッド**: 2025-2026 現在、BM25(キーワード)+ embedding(意味)を両方使うのが最強、というのが業界コンセンサス

Yamato のプロジェクトは **多言語 + 意味的検索が要件** → embedding は必須。

## 全体フロー

```
【インデックス構築時、1 回だけ】

Markdown ファイル
   ↓  Loader(Markdown なら見出しや frontmatter を意味的に読む)
Document(page_content + metadata)
   ↓  Splitter(chunk_size と overlap を決めて分割)
Document のリスト = chunks
   ↓  Embedding モデル(BGE-M3)が各 chunk をベクトル化
(ベクトル, metadata) のペア
   ↓  Vector Store(ChromaDB)に保存
永続インデックス完成

【クエリ時、毎回】

ユーザーの質問文
   ↓  同じ Embedding モデルで質問をベクトル化
クエリベクトル
   ↓  Vector Store で cosine similarity 検索、top-K 取得
関連 chunks(3-5 個)
   ↓  プロンプト組み立て(質問 + chunks)
   ↓  LLM(Gemini、既に触っている部分)
最終回答
```

**重要な観察**: インデックス構築時とクエリ時で、**Embedding モデルは同じものを使わないといけない**。空間が違うと計算が意味を失うから。BGE-M3 で index を作ったら、クエリも BGE-M3 で埋め込む。

## LangChain の抽象クラス対応表

各段階に「抽象(LangChain 共通)」と「具象(実際に使うもの)」がある:

| 段階 | 抽象クラス | 具象クラス例 |
|---|---|---|
| Load | `DocumentLoader` | `UnstructuredMarkdownLoader`, `CSVLoader`, `PyPDFLoader` |
| Split | `TextSplitter` | `RecursiveCharacterTextSplitter`, `MarkdownHeaderTextSplitter` |
| Embed | `Embeddings` | `HuggingFaceEmbeddings(BGE-M3)`, `GoogleGenerativeAIEmbeddings` |
| Store | `VectorStore` | `Chroma`, `PGVector`, `FAISS` |
| Retrieve | `Retriever` | VectorStore の `.as_retriever()` で自動生成 |
| Generate | `ChatModel` | `ChatGoogleGenerativeAI`(既に触った) |

**LangChain の価値** = この 6 段階を共通の型で繋ぐこと。BGE-M3 → OpenAI Embeddings への差し替え、Chroma → pgvector への移行、全部**具象クラスの差し替えのみ、パイプライン残り無編集**。Day 1-2 の「provider 差し替え」の思想がより高次に効いている状態。

## Yamato が実装で決めること

エンジニア判断の項目、5 つだけ:

1. **chunk_size と overlap**: 大きすぎるとノイズ増、小さすぎると文脈切れる。500-1000 文字 + 100-200 文字 overlap が定石
2. **どの Splitter**: 単純文字数(`RecursiveCharacter`)か、見出し構造尊重(`MarkdownHeader`)か
3. **Embedding モデル**: BGE-M3(既に決定済み)
4. **top_K**: 検索で何個 chunk を取るか(3-5 が典型)
5. **prompt template**: chunks をどう質問と組み立てるか

## 次に何を書くか

このオーバービューを踏まえた **Day 3 前半の実装**:

1. `src/load_markdown.py`: ネオグライスノートを Loader で読み込む
2. 返ってきた Document の `page_content` と `metadata` を print で確認
3. Splitter で chunk に分割、それぞれの中身を print で確認
4. **ここで一旦止めて、chunk が意味的にちゃんと切れているかを目視で確認**

Embed → Store → Retrieve は Day 3 後半 or Day 4 に。**Load と Split を身体に入れる**のが今日の目標。

Hello World の時と同じで「1 段階ずつ print で見て、身体で理解してから次に進む」流儀です。

---

# なぜ LangChain RAG Explorer を作るのか

> Yamato Yokoyama / 2026年8月執筆 / 更新可能な living ドキュメント
> 目的: 未来の自分・面接官・コラボレーターが「なぜ作ったか」を理解できるようにする

---

## 1. プロジェクト概要(1段落)

LangChain RAG Explorer は、多言語(日本語 / 英語、将来的にドイツ語)の個人ナレッジベースを扱う RAG システム。授業ノート、LinkedIn 投稿、Tübingen での生活記録、自己紹介 — 一人の学生の知の総体を、一つの多言語対話インターフェースで扱えるようにする。同時に、テュービンゲン大学で学ぶ Semantics & Pragmatics(意味論・語用論)の理論を、RAG / エージェントの実装として具現化する学習プロジェクトでもある。

## 2. 私(Yamato)の物語

### 起点(2020-2022年)
Temple University Japan でコンピュータサイエンスを学びながら、言語がテクノロジーで扱われる不思議さに惹かれた。日本語と英語のバイリンガル環境で育ったので、「同じことを2言語で言うとなぜニュアンスが変わるのか」という問いが常にあった。

### 転機1(2024-2025年): LinkedIn Japan Student Ambassador
学生アンバサダーとして、DeepL Japan Office ツアーを企画・実施。欧州の言語技術企業が「意味の橋渡し」を科学として本気で追いかけているのを目の当たりにした。「これがやりたいことだ」と気づく。

### 転機2(2025年10月): Tübingen大学への転入
言語技術の欧州拠点で、理論から積み上げ直す決意で、Universität Tübingen の計算言語学(ISCL)に転入。日本から欧州へ拠点を移した。

### 現在(2026年夏)
Semantics & Pragmatics の授業で Stalnaker の談話モデル、Roberts の QUD 理論、Speech Act theory を学ぶ中で、これが現代の LLM システム(RAG、エージェント、セッション管理)の背後にある問題そのものだと気づいた。

同時に、日常で使う Gemini / Claude / NotebookLM の実際の挙動 — セッションが長くなると PDF が「アップロードしてください」と再要求される、日本語検索と英語検索で違う結果が silently 出る、宿題で初めに送った PDF が後で消えている — これらの「実装上の課題」と、授業で学ぶ「理論的な談話管理の枠組み」が、同じ問題を解こうとしていることに気づいた。

## 3. なぜ今(Why now)

### 短期理由(2026年秋の応募)
- ドイツでの新卒就職(SAP 等)を目指す
- Applied AI Engineer ポジションで求められる LangChain / LangGraph / RAG / Postgres / Chainlit の実装能力を証明したい
- 参考: Ece さん(SAP Working Student)は同じスタックで内部ナレッジベース AI アシスタントを開発
  - Chat History Management, Session Persistence, User Authentication の実装
  - Kubernetes 向けドキュメント自動生成 PoC
  - AI Observability Agent(Loki + Prometheus)
  - Bachelor's thesis: Concourse CI パイプラインの root cause 分析 AI エージェント
  - Skills: LangChain, LangGraph, Alembic, SQLAlchemy, PostgreSQL, RAG, Prompt Engineering, Deep Agents, Python, GitHub Actions

### 中期理由(卒業まで)
- 日欧言語技術の橋渡しになるエンジニアとして成熟する
- SAP → DeepL → Aleph Alpha のような欧州 AI 企業でキャリアを積む

### 長期理由(卒業後)
- 日本語特有の NLP 課題(漫画翻訳、音声 AI)を、欧州で得た技術で日本に還元する
- 「計算言語学とは何か」を日本の高校生や海外進学希望者に伝えるサービスに発展させる

## 4. 広いビジョンとの接続

このプロジェクトは技術学習だけで終わらせない。将来的な発展:

- **短期**: 自分の就活のための RAG 化された自己紹介
- **中期**: 留学準備・自己分析・キャリア選択の相談ができる多言語アシスタント
- **長期**: 「NotebookLM の次」のような、コミュニティ主導の知の共有ツール

日本の LinkedIn オフィスで NotebookLM 活用講座を実施した経験もあり、このドメインは自分の話せる領域と一致する。

## 5. 理論と実装のマッピング(概要)

授業で学ぶ語用論の概念と、このプロジェクトでの実装が対応する:

| 語用論(Pragmatics) | 実装(このプロジェクト) |
|---|---|
| Common Ground | System State (Vector DB + Session Store) |
| Context Set | Search Space (retrieval で絞り込まれた候補) |
| QUD Stack | Conversation State Machine (LangGraph) |
| Implicature | Query Intent Classification (Bayesian 推論) |
| Felicity Conditions | Tool Use Pre-conditions (Agent 側) |
| Speech Act | Function Calling |

詳細は `docs/theory-mapping.md` に別途記述予定(Week 4)。

## 6. これまでの主要な設計判断(履歴)

なぜこの構成に落ち着いたか、意思決定の履歴を残す:

1. **初期案**: ドイツ留学準備支援サービスを構想
2. **絞り込み1**: NotebookLM 主体のキュレーション + 人的伴走に切り替え
3. **絞り込み2**: 「サービス開発」よりも「AI をぶん回して実装力を積む」ことを優先
4. **絞り込み3**: 日独求人分析ツールに転換(市場理解と実装練習の両立)
5. **絞り込み4**: SAP working student 応募に全振り。参考プロフィールと同型の「2つの AI アプリ + LangChain courses + LLM Challenges research」を追う
6. **確定**: 多言語個人ナレッジベース(App 1) + セッション管理(App 2) の統合 RAG。コーパスは自分自身の学習・LinkedIn・生活の記録

## 7. これまでに自分が問うてきた重要な質問

面接で必ず聞かれる「設計の理由」に対応できるよう、自問してきた質問を残す:

- **LangChain と FastAPI は何が違う?** → 「使う API」と「作る API」の違い。今回は FastAPI 不要(Chainlit が代替)
- **NotebookLM をコアに使えば楽じゃない?** → 個人開発なら十分だが、事業化と技術力証明には向かない
- **検索エンジンをゴリゴリ自作すべきか?** → 実装力の証明にはなるが、RAG 構築の方が今の就活には効く
- **サービスと技術のどちらを先にやる?** → 技術を成熟させてから、が正解
- **Gemini が「もう一度アップして」と言うのはなぜ?** → LLM の Attachment Stripping(コスト削減のための添付削除)。これを解決するのが本プロジェクトの Session Management 層
- **なぜ授業スライドで多言語 RAG だと NotebookLM で済むと言われるのか?** → 「自分の学習・生活・キャリアの統合ナレッジベース」というコーパスにすることで、NotebookLM には作れない一貫性を持たせる
- **なぜ Gemini API か? 他の LLM は?** → 学生プランとの親和性 + Flash 無料枠が広い。ただし LangChain 経由なので後で差し替え可能
- **なぜ多言語埋め込み(BGE-M3)か?** → 同じ意味を持つ日英独文が近いベクトルになる性質 = クロス言語検索の要
- **API プログラミングは学ばなくていいのか?** → 直接叩く経験は最小限。LangChain がラップする。ただし「API とは何か」の概念理解は必須

---

## 8. 関連ドキュメント(専門性・試験対策・学習方針)

このファイルは「なぜこのプロジェクトを作るか」に専念させるため、2026-08-27に議論した以下のトピックは別ファイルに分割した:


---

このファイルは進行とともに更新される。新しい設計判断があるたびに追記する。

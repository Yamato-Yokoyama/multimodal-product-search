"""
src/embedding_quality_test.py

embed_test.py は「目で見て確認する」スクリプトのまま残す(PCA可視化などexploration
としての価値があるので変更しない)。このファイルは新規で、assertを持つ
「機械的に判定する」テストにする。GitHub Actions 101(docs/notes/github-actions-101-tutorial/
01_why_and_what.md)で話した「lintは書き方チェック、testは振る舞いチェック」の
「振る舞い」側をここで書く。

詰まったら聞く。ここでは「何をすべきか」だけを Input/Output/なぜ で示す。
中身は自分で書く。背景は:
  - docs/notes/langchain-and-rag-overview.md:136 (chunk_sizeの定石: 500-1000文字)
  - docs/data-flow/markdown-neo-gricean.md (Chunk Size希釈の実例)

注意(なぜembed_test.pyをimportしないか):
  embed_test.pyはトップレベルにコードが書いてあるスクリプト形式なので、
  importすると plt.show() まで含めて全部実行されてしまう。
  なのでこのファイルでは、ロード〜埋め込みまでの最小限の手順を
  fixtureとして独立に書く(embed_test.pyの該当部分を見ながら真似ていい)。

Called by: pytest(`pytest src/embedding_quality_test.py`)
Depends on: pytest(**未インストール**。`pip install pytest`した上で
            `pip freeze > requirements.txt`しておくこと。他の依存と同じく
            バージョン決め打ちで手書きしない)
"""
import numpy as np
import pytest

from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings


FILEPATH = "data/class-notes/neo-gricean-implicature.md"
EXPECTED_DIM = 1024
# 定石: docs/notes/langchain-and-rag-overview.md:136 の「500-1000文字」を上限の目安にする
MAX_CHUNK_CHARS = 1000
MIN_CHUNK_CHARS = 15  # 見出しだけ、みたいな短すぎるchunk(ノイズ)を弾く下限


def cosine_similarity(a, b) -> float:
    # embed_test.pyの同名関数と同じ実装でいい(コピーでOK、共通化は今回はやらない)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# ============================================================
# fixture: 全テスト関数が共通して使う「ロード→分割→埋め込み」の下準備。
#
# pytestのfixtureとは: 複数のtest関数が必要とする準備処理を1箇所にまとめ、
# test関数の引数名にfixture名(下の例だと chunks_and_vectors)を書くだけで
# pytestが自動的にその戻り値を渡してくれる仕組み。
# scope="module"を指定すると、このファイル内で1回だけ実行されて使い回される
# (BGE-M3のロードは重いので、test関数ごとに毎回re-loadしないようにする)。
# ============================================================
@pytest.fixture(scope="module")
def chunks_and_vectors():
    """Neo-Gricean note を読み込み→分割→埋め込みまで実行し、両方を返す。

    Output:
        tuple[list[Document], list[list[float]]] -- (split_docs, vectors)

    なぜ:
        下の全test関数が「同じ分割・埋め込み結果」を土台に、それぞれ違う
        観点(次元数/チャンク数/チャンクサイズ/決定論性/ランキング)を確認する。
        埋め込みの実行(重い)を1回にまとめるためfixture化する。
    """
    # TODO 1: embed_test.pyのLoad〜Embed部分(1〜68行目あたり)を参考に、
    #   同じ手順をここに書く。
    #   ヒント:
    #   1. Path(FILEPATH).read_text(encoding="utf-8") でファイルを読む
    #   2. Document(page_content=..., metadata={"source": FILEPATH}) を1個作る
    #   3. MarkdownHeaderTextSplitter(headers_to_split_on=[("#","Header 1"),("##","Header 2"),("###","Header 3")])
    #      で .split_text(doc.page_content)
    #   4. HuggingFaceEmbeddings(model_name="BAAI/bge-m3", model_kwargs={"device": "cpu"})
    #      を作り、.embed_documents([d.page_content for d in split_docs])
    #   5. return (split_docs, vectors)
    ...
    Path(FILEPATH).read_text(encoding="utf-8")
    doc = Document(page_content=Path(FILEPATH).read_text(encoding="utf-8"), metadata={"source": FILEPATH})
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#","Header 1"),("##","Header 2"),("###","Header 3")])
    split_docs = splitter.split_text(doc.page_content)
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", model_kwargs={"device": "cpu"})
    vectors = embeddings.embed_documents([d.page_content for d in split_docs])
    return (split_docs, vectors)


# ============================================================
# 見本(参考実装): 次元数だけを確認する、一番シンプルな形。
# ============================================================
def test_embedding_dimension(chunks_and_vectors):
    """埋め込みベクトルが期待通り1024次元か。

    Input:
        chunks_and_vectors: fixtureが返す (split_docs, vectors)

    Output:
        なし。assertが通ればpass、通らなければpytestが自動でfailにする

    なぜ:
        BGE-M3は常に1024次元を返すはず、という「あらかじめ分かっている
        期待される答え」をassert1行で機械的に確認する、一番単純な例。
    """
    _, vectors = chunks_and_vectors
    assert len(vectors[0]) == EXPECTED_DIM


# ============================================================
# ここから下が今回のTODO。上の見本と同じ形(fixtureを引数で受け取り、
# assertする)で、観点だけ変えて4つ書く。
# ============================================================

# TODO 2: チャンク数が0でないことを確認するテスト
#   関数名の例: test_chunk_count_is_positive(chunks_and_vectors)
#   ヒント: split_docs, _ = chunks_and_vectors のあと len(split_docs) > 0 をassert。
#   「分割ロジックが壊れて0件になった」という事故を拾うための、一番地味だが大事なテスト。
def test_chunk_count_is_positive(chunks_and_vectors):
    """チャンク数が0でないことを確認するテスト。

    Input:
        chunks_and_vectors: fixtureが返す (split_docs, vectors)

    Output:
        なし。assertが通ればpass、通らなければpytestが自動でfailにする

    なぜ:
        「分割ロジックが壊れて0件になった」という事故を拾うための、一番地味だが大事なテスト。
    """
    split_docs, _ = chunks_and_vectors
    assert len(split_docs) > 0


# TODO 3: 各チャンクの文字数が MIN_CHUNK_CHARS 〜 MAX_CHUNK_CHARS に収まっているかのテスト
#   関数名の例: test_chunk_size_within_bounds(chunks_and_vectors)
#   ヒント: split_docsを1個ずつforループし、len(doc.page_content) が
#   MIN_CHUNK_CHARS以上MAX_CHUNK_CHARS以下かをassertする。
#   これは「メタレイヤー」のテスト(埋め込みベクトルの中身ではなく、
#   分割の"形"そのものを見ている)。
#   注意: 今のNeo-Griceanノートに対して実行すると、Chunk Size希釈の原因になった
#   「定義+例+補足が全部入った長いchunk」がMAX_CHUNK_CHARSを超えて
#   **failする可能性が高い**。これは意図した挙動 -
#   「過去に見つかった実際のバグを、テストとして固定化した(先にfailするテストを
#   書く、というTDDの実例)」という扱いでOK。failしたままでも一旦コミットしていい。
def test_chunk_size_within_bounds(chunks_and_vectors):
    """各チャンクの文字数が指定された範囲内であることを確認するテスト。

    Input:
        chunks_and_vectors: fixtureが返す (split_docs, vectors)

    Output:
        なし。assertが通ればpass、通らなければpytestが自動でfailにする

    なぜ:
        チャンクのサイズが適切であることを保証するため。
    """
    split_docs, _ = chunks_and_vectors
    for doc in split_docs:
        assert MIN_CHUNK_CHARS <= len(doc.page_content) <= MAX_CHUNK_CHARS

# TODO 4: 同じクエリを2回embed_queryして、ほぼ同じベクトルが返るかのテスト
#   関数名の例: test_embedding_is_deterministic(chunks_and_vectors)
#   ヒント: chunks_and_vectorsは使わず、この中で新しくembeddingsを作る必要はない
#   (fixtureが持ってるembeddings自体はreturnしていないので、必要なら
#   TODO 1のfixtureの戻り値にembeddingsも含めるよう変更してよい)。
#   query = "Q-principleって何" を2回 embed_query() し、
#   np.allclose(vec1, vec2) で比較する(完全一致ではなく、浮動小数点の
#   ごくわずかな誤差を許容するための関数)。
def test_embedding_is_deterministic(chunks_and_vectors):
    """同じクエリを2回埋め込み、ほぼ同じベクトルが返ることを確認するテスト。

    Input:
        chunks_and_vectors: fixtureが返す (split_docs, vectors)

    Output:
        なし。assertが通ればpass、通らなければpytestが自動でfailにする

    なぜ:
        埋め込みモデルが決定論的であることを保証するため。
    """
    query = "Q-principleって何"
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", model_kwargs={"device": "cpu"})
    vec1 = embeddings.embed_query(query)
    vec2 = embeddings.embed_query(query)
    assert np.allclose(vec1, vec2)


# TODO 5(一番難しい、任意): 関連するchunkが無関係なchunkより上位に来るかのテスト
#   関数名の例: test_relevant_chunk_ranks_above_unrelated_chunk(chunks_and_vectors)
#   ヒント:
#   - query = "Q-principleって何" を用意し、embed_query()でベクトル化
#   - split_docsの中から、doc.metadataのHeaderを見て
#     「明らかにQ-principleに関するchunk」と「明らかに無関係なchunk」を
#     1個ずつ選ぶ(インデックス決め打ちでいい)
#   - cosine_similarity(query_vec, 関連chunkのvector) が
#     cosine_similarity(query_vec, 無関係chunkのvector) より大きいことをassert
#   注意: docs/data-flow/markdown-neo-gricean.mdに記録されている通り、
#   実際にQ-principle chunkが5位まで落ちた実例があるので、このテストも
#   現状のチャンク分割ではfailする可能性がある。TODO 3と合わせて両方failするなら、
#   それ自体が「Chunk Size希釈は実在する」ことの動かぬ証拠になる。
def test_relevant_chunk_ranks_above_unrelated_chunk(chunks_and_vectors):
    """関連するチャンクが無関係なチャンクより上位にランクされることを確認するテスト。

    Input:
        chunks_and_vectors: fixtureが返す (split_docs, vectors)

    Output:
        なし。assertが通ればpass、通らなければpytestが自動でfailにする

    なぜ:
        埋め込みのランキングが期待通りであることを保証するため。
    """
    query = "Q-principleって何"
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", model_kwargs={"device": "cpu"})
    query_vec = embeddings.embed_query(query)

    split_docs, vectors = chunks_and_vectors

    # 明らかにQ-principleに関するchunkと無関係なchunkを選ぶ
    relevant_index = next(i for i, doc in enumerate(split_docs) if "Q-principle" in doc.metadata.get("Header 3", ""))
    unrelated_index = next(i for i, doc in enumerate(split_docs) if "参考文献" in doc.metadata.get("Header 2", ""))

    relevant_score = cosine_similarity(query_vec, vectors[relevant_index])
    unrelated_score = cosine_similarity(query_vec, vectors[unrelated_index])

    assert relevant_score > unrelated_score

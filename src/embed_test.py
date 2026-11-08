import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import japanize_matplotlib  # noqa: F401


# 1. UnstructuredMarkdownLoader → UnstructuredLoader(統合版)
from langchain_unstructured import UnstructuredLoader
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings


FILEPATH = "data/class-notes/neo-gricean-implicature.md"
# 1. Load: Markdown ファイルを読み込む

# --- 昨日の Load ---
def load_as_plain_text(filepath: str) -> list[Document]:
    """
    Markdown ファイルを読み、Document 1 個の list として返す素朴なローダー。
    
    Input:
        filepath: str - Markdown ファイルの絶対 or 相対パス
    
    Output:
        list[Document] - 要素 1 個のリスト
                         doc.page_content = ファイル全文
                         doc.metadata = {"source": filepath}
    
    なぜ:
        - LangChain の Loader は必ず list を返す規則(将来複数ファイル対応時に扱いが同じ)
        - UnstructuredLoader が Markdown で崩れたため、自作でシンプルに保つ
    """
    text = Path(filepath).read_text(encoding="utf-8")
    return [Document(page_content=text, metadata={"source": filepath})]

docs = load_as_plain_text(FILEPATH)

# 2. Split: Markdown 見出しで chunks に分割

# --- 昨日の Split ---
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)

split_docs = splitter.split_text(docs[0].page_content)

# 3. Embed: BGE-M3 で 12 chunks を 1024 次元ベクトル化

# --- 今日の Embed ---
# embedding = ChatGoogleGenerativeAI().embed_documents(split_docs)
embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-m3",
    model_kwargs={"device": "cpu"}
)

vectors = embeddings.embed_documents([doc.page_content for doc in split_docs])

print(f"Chunk: {len(split_docs)}")
print(f"Vectors: {len(vectors)}")
print(f"Vector dim: {len(vectors[0])}")


#Visual
X = np.array(vectors)

#PCA
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X) # shape (12,2  )

#plot
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(X_2d[:, 0], X_2d[:, 1], s=100) #scatterの引数は、 (x座標, y座標, サイズ)

for i, doc in enumerate(split_docs):
    label = doc.metadata.get("Header 3") or doc.metadata.get("Header 2") or doc.metadata.get("Header 1", f"chunk{i}")
    ax.annotate(label[:20], (X_2d[i, 0], X_2d[i, 1]), fontsize=8)

ax.set_xlabel(f"PC1 (説明分散 {pca.explained_variance_ratio_[0]:.1%})")
ax.set_ylabel(f"PC2 (説明分散 {pca.explained_variance_ratio_[1]:.1%})")
ax.set_title("Neo-Gricean chunks in embedding space (PCA 2D)")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("data/embedding_pca.png", dpi=150)
plt.show()


#2026-08-11
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 4. Query: クエリを 1 個ベクトル化
query="Q-principleって何"
query_vec = embeddings.embed_query(query)

# 5. Similarity: cosine で 12 chunks とスコアリング

scores = []

for chunkvec, doc in zip(vectors, split_docs):
    similarity = cosine_similarity(query_vec, chunkvec)
    scores.append((similarity, doc))
    
scores.sort(reverse=True, key=lambda x: x[0])

# 6. Rank: 上位 3 個を表示

for score, doc in scores[:3]:
    print(f"\nScore: {score:.4f}")
    print(f"Metadata: {doc.metadata}")
    print(f"Content: {doc.page_content[:150]}")
"""
src/similarity.py

ベクトル間の類似度計算ユーティリティ。
プロバイダ非依存(numpy のみ使用)、embedding モデルを差し替えても影響なし。
"""

import numpy as np

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    
    """
    2 つのベクトルのコサイン類似度を返す。
    
    Input:
        a, b: numpy 配列(shape (dim,) 同一)
    
    Output:
        float, -1.0 〜 1.0 の範囲
        1.0 = 完全に同方向、0.0 = 直交、-1.0 = 逆方向
    
    なぜ:
        - RAG では「意味の方向」を測るので長さの影響を消したい
        - Euclidean distance より embedding 業界標準
        - BGE-M3 含む現代の embedding モデルは cosine 前提で訓練済み
    """
    
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))



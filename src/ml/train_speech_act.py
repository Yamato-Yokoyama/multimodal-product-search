"""
src/ml/train_speech_act.py

Issue #39: DailyDialogでSpeech Act分類のbaselineを2種類(Naive Bayes /
Logistic Regression)学習する。データセットは分類器の重みを学習するための
教科書としてのみ使う(RAG側の検索対象コーパスとは無関係)。

参考: docs/speech-act-baseline-primer.md(言語学的知見・ML基礎の予習ノート)

Called by: notebooks/01_speech_act_baseline.ipynb, src/ml/inference.py(学習済みモデル)
Depends on: datasets, scikit-learn, joblib
"""
from pathlib import Path

import joblib
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODELS_DIR = Path(__file__).parent / "models"

# li2017dailydialog/daily_dialog の act ラベル(0=__dummy__は実データに出現しない)
ACT_LABELS = {1: "inform", 2: "question", 3: "directive", 4: "commissive"}


def load_speech_act_data():
    """DailyDialogを発話単位にflattenし、train/val/testのテキスト・ラベル配列を返す。

    Output:
        (X_train, y_train, X_val, y_val, X_test, y_test)
        X_*: 発話文字列のlist、y_*: act ラベル文字列("inform"等)のlist

    なぜ:
        DailyDialogは1行1対話(発話のlist + actのlist)という構造なので、
        分類器の学習に使うには発話単位に平坦化する必要がある。
        新しいdatasetsライブラリはdataset scriptを許可しないため、
        li2017dailydialog/daily_dialog を refs/convert/parquet で読む
        (docs/speech-act-baseline-primer.md 参照)。
    """
    ds = load_dataset("li2017dailydialog/daily_dialog", revision="refs/convert/parquet")

    def _flatten(split):
        texts, labels = [], []
        for dialog, acts in zip(ds[split]["dialog"], ds[split]["act"]):
            for utterance, act in zip(dialog, acts):
                texts.append(utterance)
                labels.append(ACT_LABELS[act])
        return texts, labels

    X_train, y_train = _flatten("train")
    X_val, y_val = _flatten("validation")
    X_test, y_test = _flatten("test")
    return X_train, y_train, X_val, y_val, X_test, y_test


def train_naive_bayes(X_train, y_train) -> Pipeline:
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
        ("clf", MultinomialNB()),
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def train_logistic_regression(X_train, y_train) -> Pipeline:
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def evaluate(pipeline: Pipeline, X_test, y_test, label: str) -> dict:
    """test setで評価し、classification_reportを表示、macro F1を返す。"""
    y_pred = pipeline.predict(X_test)
    print(f"=== {label} ===")
    print(classification_report(y_test, y_pred, digits=3))
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    print(f"{label} macro F1: {macro_f1:.3f}\n")
    return {"macro_f1": macro_f1, "y_pred": y_pred}


if __name__ == "__main__":
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading DailyDialog...")
    X_train, y_train, X_val, y_val, X_test, y_test = load_speech_act_data()
    print(f"train={len(X_train)} val={len(X_val)} test={len(X_test)}")

    nb_pipeline = train_naive_bayes(X_train, y_train)
    nb_result = evaluate(nb_pipeline, X_test, y_test, "Naive Bayes (TF-IDF)")
    joblib.dump(nb_pipeline, MODELS_DIR / "nb_speech_act.joblib")

    lr_pipeline = train_logistic_regression(X_train, y_train)
    lr_result = evaluate(lr_pipeline, X_test, y_test, "Logistic Regression (TF-IDF)")
    joblib.dump(lr_pipeline, MODELS_DIR / "lr_speech_act.joblib")

    print(f"Saved models to {MODELS_DIR}/")

"""
src/ml/inference.py

学習済みSpeech Act分類器(Naive Bayes / Logistic Regression)を読み込んで
推論するラッパー。Issue #39時点ではagent/routerには繋がず、単体で動く形。

Called by: notebooks/01_speech_act_baseline.ipynb(将来的にはsrc/agent/, Issue #39のNon-goals参照)
Depends on: joblib
"""
from pathlib import Path

import joblib


class SpeechActClassifier:
    def __init__(self, model_path: Path):
        self.pipeline = joblib.load(model_path)

    def predict(self, utterance: str) -> str:
        return self.pipeline.predict([utterance])[0]

    def predict_proba(self, utterance: str) -> dict:
        probs = self.pipeline.predict_proba([utterance])[0]
        return dict(zip(self.pipeline.classes_, probs))


if __name__ == "__main__":
    models_dir = Path(__file__).parent / "models"
    clf = SpeechActClassifier(models_dir / "lr_speech_act.joblib")

    for utterance in [
        "Could you close the window?",
        "I will send the report by tomorrow.",
        "What time does the train leave?",
        "It was raining all day yesterday.",
    ]:
        print(f"{utterance!r} -> {clf.predict(utterance)} {clf.predict_proba(utterance)}")

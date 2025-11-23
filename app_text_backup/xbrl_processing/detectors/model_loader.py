# detectors/model_loader.py
from sentence_transformers import SentenceTransformer

_model = None

def get_model():
    global _model
    if _model is None:
        # You can change model name if you want a smaller one
        _model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")
    return _model
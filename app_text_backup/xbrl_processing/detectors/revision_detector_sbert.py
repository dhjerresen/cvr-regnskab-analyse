# detectors/revision_detector_sbert.py
"""
SBERT-based semantic classification for Danish auditor statements.
"""

from sentence_transformers import util
from .model_loader import get_model

# Reference texts for each revision type
revision_refs = {
    "Ingen bistand": [
        "Ingen bistand",
        "Ingen revision eller review udført"
    ],
    "Assistance": [
        "Vi har opstillet årsregnskabet for selskabet",
        "opstilling af finansielle oplysninger",
        "vi har assisteret med opstilling"
    ],
    "Udvidet gennemgang": [
        "Erklæring om udvidet gennemgang",
        "Vi har udført udvidet gennemgang af årsregnskabet",
        "revisor har udført udvidet gennemgang"
    ],
    "Revision": [
        "Vi har revideret årsregnskabet",
        "Vi har udført vores revision i overensstemmelse med internationale standarder om revision",
        "Revisors ansvar for revisionen af årsregnskabet"
    ],
}

# Flatten reference texts and labels
ref_texts = []
ref_labels = []
for label, texts in revision_refs.items():
    ref_texts.extend(texts)
    ref_labels.extend([label] * len(texts))

_ref_embeddings = None  # cached embeddings


def _get_ref_embeddings():
    """Encode reference texts once and cache."""
    global _ref_embeddings
    if _ref_embeddings is None:
        model = get_model()
        _ref_embeddings = model.encode(ref_texts, convert_to_tensor=True)
    return _ref_embeddings


def detect_revision_type_sbert(text: str, return_score: bool = False):
    """
    Detects revision type from text using SBERT semantic similarity.

    Args:
        text (str): Input text (e.g. auditor section).
        return_score (bool): If True, returns (label, score).

    Returns:
        str | (str, float)
    """
    if not text or len(text.strip()) < 10:
        return ("Ukendt", 0.0) if return_score else "Ukendt"

    model = get_model()
    ref_embeddings = _get_ref_embeddings()

    text_emb = model.encode(text, convert_to_tensor=True)
    scores = util.cos_sim(text_emb, ref_embeddings)

    best_idx = scores.argmax().item()
    best_label = ref_labels[best_idx]
    best_score = scores.max().item()

    return (best_label, best_score) if return_score else best_label
# detectors/going_concern_detector.py
"""
SBERT-based detection of going concern uncertainty.
"""

from sentence_transformers import util
from .model_loader import get_model

POSITIVE_EXAMPLES = [
    "der er betydelig usikkerhed om selskabets evne til at fortsætte driften",
    "selskabet er i økonomiske vanskeligheder og der er going concern usikkerhed",
    "egenkapitalen er tabt",
    "kapitalen er tabt og driften er usikker",
    "der er tvivl om selskabets fortsatte drift",
    "revisor fremhæver usikkerhed om going concern",
    "supplerende oplysninger vedrørende going concern",
    "material uncertainty related to going concern",
    "virksomheden har negativ egenkapital",
    "kapitaltab og økonomisk usikkerhed",
]

NEGATIVE_EXAMPLES = [
    "der er ikke usikkerhed om going concern",
    "ledelsen vurderer at forudsætningen om fortsat drift er opfyldt",
    "ingen væsentlig usikkerhed om virksomhedens drift",
]

_POS_EMB = None
_NEG_EMB = None


def _get_reference_embeddings():
    global _POS_EMB, _NEG_EMB
    if _POS_EMB is None or _NEG_EMB is None:
        model = get_model()
        _POS_EMB = model.encode(POSITIVE_EXAMPLES, convert_to_tensor=True)
        _NEG_EMB = model.encode(NEGATIVE_EXAMPLES, convert_to_tensor=True)
    return _POS_EMB, _NEG_EMB


def detect_going_concern(texts: list[str]) -> bool:
    """
    Returns True if there are indications of going concern uncertainty.
    """

    if not texts:
        return False

    model = get_model()
    POS_EMB, NEG_EMB = _get_reference_embeddings()

    combined = " ".join(texts).lower()
    if len(combined.strip()) < 30:
        return False

    text_emb = model.encode(combined, convert_to_tensor=True)

    pos_score = float(util.cos_sim(text_emb, POS_EMB).max())
    neg_score = float(util.cos_sim(text_emb, NEG_EMB).max())

    if neg_score > 0.50 and neg_score > pos_score:
        return False
    if pos_score > 0.55:
        return True

    return False

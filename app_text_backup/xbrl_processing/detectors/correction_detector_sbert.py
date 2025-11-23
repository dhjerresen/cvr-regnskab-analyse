# detectors/correction_detector_sbert.py
"""
SBERT-based semantic detection of significant error corrections.
"""

from sentence_transformers import util
from .model_loader import get_model

POSITIVE_EXAMPLES = [
    "Der er foretaget korrektion af en væsentlig fejl",
    "Tidligere års tal er korrigeret",
    "Tidligere års fejloplysninger er rettet",
    "Sammenligningstal er korrigeret",
    "Der er sket en ændring som følge af en fejl",
    "Der er foretaget regulering af tidligere års tal",
    "Regnskabet er korrigeret som følge af fejl",
    "En fejl er opdaget og rettet i år",
]

NEGATIVE_EXAMPLES = [
    "Der er ikke foretaget korrektion af fejl",
    "Ingen korrektion er foretaget",
    "Der er ingen væsentlige fejl",
    "Ingen fejl er fundet",
    "Der er ikke korrigeret tidligere års fejl",
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


def detect_significant_error_sbert(texts: list[str]) -> bool:
    """
    Returns True if there are indications of correction of significant error.
    """

    if not texts:
        return False

    model = get_model()
    POS_EMB, NEG_EMB = _get_reference_embeddings()

    combined = " ".join(texts)
    if len(combined.strip()) < 30:
        return False

    text_emb = model.encode(combined, convert_to_tensor=True)

    pos_score = float(util.cos_sim(text_emb, POS_EMB).max())
    neg_score = float(util.cos_sim(text_emb, NEG_EMB).max())

    # Negative wording dominates → explicitly no correction
    if neg_score > 0.50 and neg_score > pos_score:
        return False

    # Positive correction signal strong enough
    if pos_score > 0.55:
        return True

    return False

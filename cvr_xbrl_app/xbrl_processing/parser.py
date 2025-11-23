# xbrl_processing/parser.py
from .arelle_loader import load_model
from .fact_extractor import get_fact

from .taxonomy_map import (
    REVISION_TYPE,
    AUDITOR_DESCRIPTION,
    MAIN_ACTIVITY,
    MATERIAL_ERROR_CORRECTION,
    GOING_CONCERN,
    ACCOUNTING_CLASS,
    ACCOUNTING_CLASS_UPGRADE,
)

def _find_first(model, names):
    """Helper: return first matching fact from a set of localNames."""
    for name in names:
        val = get_fact(model, name)
        if val:
            return val
    return None

def _clean_activity(text: str) -> str:
    if not text:
        return text

    # Remove soft hyphens and weird invisible characters
    text = text.replace("\u00AD", "")   # soft hyphen
    text = text.replace("\u2011", "-")  # non-breaking hyphen

    # Normalize whitespace
    t = " ".join(text.split())

    # Case 1 — prefix at the beginning
    prefix = "Selskabets væsentligste aktiviteter"
    if t.startswith(prefix):
        t = t[len(prefix):].lstrip(" .")

    # Case 2 — prefix concatenated inside the string ("aktiviteterSelskabets")
    t = t.replace(prefix + " ", "")
    t = t.replace(prefix, "")

    # Final trim
    return t.strip()


def extract_xbrl_data(filepath: str) -> dict:
    """
    Parse XBRL/iXBRL file with Arelle and extract general qualitative facts.
    No ML, no SBERT — pure taxonomy-based extraction.
    """
    try:
        model = load_model(filepath)

        data = {
            # Revision info
            "Revisionstype": _find_first(model, REVISION_TYPE),
            "Revisortype": _find_first(model, AUDITOR_DESCRIPTION),

            # Company activity description
            "Væsentlig aktivitet": _clean_activity(_find_first(model, MAIN_ACTIVITY)),

            # Corrections of material errors
            "Korrektion af væsentlig fejl": _find_first(model, MATERIAL_ERROR_CORRECTION),

            # Going concern
            "Going concern usikkerhed": _find_first(model, GOING_CONCERN),

            # Accounting class
            "Anvendt regnskabsklasse": _find_first(model, ACCOUNTING_CLASS),

            # Optional use of higher accounting class
            "Tilvalg af højere regnskabsklasse": _find_first(model, ACCOUNTING_CLASS_UPGRADE),
        }

        return data

    except Exception as e:
        print("[Fejl] XBRL parsing:", e)
        return {"Fejl": str(e)}

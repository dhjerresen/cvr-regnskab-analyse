# detectors/auditor_type_detector.py

import re
from rapidfuzz import fuzz


def normalize(text: str) -> str:
    """
    Robust text normalizer that:
      - lowercases text
      - removes non-breaking spaces, soft hyphens, zero-width chars
      - fixes missing spaces between glued-together words
      - collapses repeated whitespace
    """
    if not text:
        return ""

    # Lowercase
    t = text.lower()

    # Remove weird whitespace characters
    t = t.replace("\u00a0", " ")   # non-breaking space
    t = t.replace("\u200b", "")    # zero-width space
    t = t.replace("\u00ad", "")    # soft hyphen

    # Fix words smashed together: "larsenRegistreret"
    t = re.sub(r"([a-zæøå])([A-ZÆØÅ])", r"\1 \2", t, flags=re.UNICODE)

    # Collapse multiple spaces
    t = re.sub(r"\s+", " ", t)

    return t.strip()


def detect_auditor_type(text: str) -> str:
    """
    Detects auditor type from ANY messy XBRL text dump.
    Works with glued text, broken formatting, and OCR-like output.
    """

    t = normalize(text)

    # --- Exact matches (most reliable) ---
    if "statsautoriseret revisor" in t:
        return "Statsautoriseret revisor"

    if "registreret revisor" in t or "godkendt revisor" in t:
        return "Registreret revisor"

    # --- Fuzzy detection for OCR errors ---
    if fuzz.partial_ratio("registreret revisor", t) > 85:
        return "Registreret revisor"

    if fuzz.partial_ratio("statsautoriseret revisor", t) > 85:
        return "Statsautoriseret revisor"

    # --- Generic fallback: any revisor reference ---
    if "revisor" in t:
        return "Revisor"

    return "Ingen bistand"
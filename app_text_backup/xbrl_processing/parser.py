"""
parser.py
----------
Robust parser for Inline XBRL (iXBRL) files.
These files are HTML with <ix:*> tags.

We extract all visible text from the HTML and feed it into SBERT detectors.
"""

import re

from bs4 import BeautifulSoup

from .detectors.revision_detector_sbert import detect_revision_type_sbert
from .detectors.auditor_type_detector import detect_auditor_type
from .detectors.activity_extractor import extract_main_activity
from .detectors.correction_detector_sbert import detect_significant_error_sbert
from .detectors.going_concern_detector import detect_going_concern

# ------------------------------------------------------------
# Load file as raw text
# ------------------------------------------------------------
def _load_raw_text(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ------------------------------------------------------------
# Extract visible text from iXBRL HTML
# ------------------------------------------------------------
def _extract_visible_text(raw_html: str) -> list[str]:
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script/style
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Extract visible text
    text = soup.get_text(separator=" ")

    # Normalize
    text = re.sub(r"\s+", " ", text)

    # Split into chunks/sentences
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in chunks if len(c.strip()) > 20]


# ------------------------------------------------------------
# MAIN PARSER
# ------------------------------------------------------------
def extract_xbrl_data(filepath: str) -> dict:
    try:
        # 1. Load HTML/iXBRL
        raw_text = _load_raw_text(filepath)

        # 2. Extract visible text chunks
        all_texts = _extract_visible_text(raw_text)

        data = {}

        # 3. Revisionstype (SBERT)
        best_label = "Ukendt"
        best_score = 0.0

        for t in all_texts:
            label, score = detect_revision_type_sbert(t, return_score=True)
            if score > best_score:
                best_label = label
                best_score = score

        data["Revisionstype"] = best_label

        # 4. Revisortype
        data["Revisortype"] = detect_auditor_type(raw_text)

        # 5. Væsentlig aktivitet
        data["Væsentlig aktivitet"] = extract_main_activity(all_texts)

        # 6. Korrektion
        data["Korrektion af væsentlig fejl"] = detect_significant_error_sbert(all_texts)

        # 7. Going concern
        data["Going concern usikkerhed"] = detect_going_concern(all_texts)

        return data

    except Exception as e:
        print("[Fejl] XBRL parsing:", e)
        return {"Fejl": str(e)}

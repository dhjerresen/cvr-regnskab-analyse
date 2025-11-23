# detectors/activity_extractor.py

import re

PATTERNS = [
    r"selskabets væsentligste aktiviteter[^.]*\.",
    r"selskabets væsentligste aktivitet[^.]*\.",
    r"selskabets aktiviteter består[^.]*\.",
    r"selskabets aktiviteter omfatter[^.]*\.",
    r"virksomhedens væsentligste aktiviteter[^.]*\.",
    r"virksomhedens væsentligste aktivitet[^.]*\.",
    r"virksomheden beskæftiger sig[^.]*\.",
    r"virksomhedens aktiviteter[^.]*\.",
    r"formålet med selskabet[^.]*\."
]


def clean_activity(text: str) -> str:
    """
    Cleans common repetition/duplication problems in XBRL activity text.
    """
    t = text.strip()

    # Remove duplicated starts like:
    # "Selskabets væsentligste aktiviteter Selskabets væsentligste aktiviteter består i"
    t = re.sub(
        r"(selskabets væsentligste aktiviteter\s+){2,}",
        "selskabets væsentligste aktiviteter ",
        t,
        flags=re.IGNORECASE
    )

    # Remove accidental double spaces
    t = re.sub(r"\s+", " ", t)

    return t.strip(" .,")


def extract_main_activity(texts: list[str]) -> str | None:
    """
    Extracts the company's main activity from XBRL text blocks.
    Uses rule-based patterns that match typical Danish SME phrasing.
    """

    if not texts:
        return None

    combined = " ".join(texts)
    combined = re.sub(r"\s+", " ", combined)

    # Try all patterns
    for pat in PATTERNS:
        m = re.search(pat, combined, flags=re.IGNORECASE)
        if m:
            return clean_activity(m.group(0))

    return None

# xhtml_text.py
"""
Robust XHTML/iXBRL narrative extractor for Danish annual reports (ESEF).

Goals:
- Extract human-readable narrative text from XHTML/iXBRL
- Preserve headings (h1-h6) clearly so LLM can detect sections
- Keep paragraph structure (blank lines between blocks)
- Remove most technical / numeric-only noise

Usage:
    text = extract_raw_text("/path/to/report.xhtml")
"""

from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from bs4.element import Tag
import re
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ------------------------------------------------------------
# TAGS that usually contain readable narrative text
# ------------------------------------------------------------
BLOCK_TAGS = [
    "p",
    "div",
    "section",
    "article",
    "li",
    "td",
    "span",
    "ix:nonNumeric",
    "ix:continuation",
    "ix:nonFraction",
    "xhtml:p",
    "xhtml:div",
    "text:p",
]

HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]

# These words will likely appear in or near the Management Review
HEADING_MARKERS = [
    "ledelsesberetning",
    "koncernledelsesberetning",
    "brev til vores aktionærer",
    "brev til aktionærer",
    "vores bank",
    "letter to shareholders",
    "management review",
]


# ------------------------------------------------------------
# CLEANING HELPERS
# ------------------------------------------------------------
def _looks_like_table_or_number_line(text: str) -> bool:
    """
    Return True if the line looks like pure numeric / table data.
    We do NOT want to drop headings and normal narrative here.
    """
    t = text.strip()
    if not t:
        return True

    # Only digits, punctuation, whitespace (typical table cells)
    if re.fullmatch(r"[\d\.,()%\s\-]+", t):
        return True

    # Very short fragments like "2023", "1,234" etc.
    if len(t) <= 3 and re.fullmatch(r"[\d\s]+", t):
        return True

    return False


def clean_line(text: str, is_heading: bool = False) -> str:
    """
    Clean individual narrative lines.

    - Collapse whitespace
    - Strip namespace noise in a gentle way
    - Remove obvious XBRL member codes
    - Skip numeric-only lines (except headings)
    """
    t = text.strip()
    if not t:
        return ""

    # Basic whitespace normalization
    t = re.sub(r"\s+", " ", t)

    # Remove VERY noisy namespace-like artifacts,
    # but keep most of the human text intact.
    # We keep words that contain letters.
    # Example: "dk:Ledelsesberetning" -> "Ledelsesberetning"
    t = re.sub(r"\b([A-Za-z0-9]+:)([A-Za-zÆØÅæøå].*?)", r"\2", t)

    # Remove member codes like "mne40726"
    t = re.sub(r"\b[a-z]{3,8}\d{3,8}\b", "", t)

    # Heading: keep even if mostly numeric (e.g. "1 Ledelsesberetning")
    if is_heading:
        return t.strip()

    # Non-heading: filter out numeric-only / table-like lines
    if _looks_like_table_or_number_line(t):
        return ""

    return t.strip()


# ------------------------------------------------------------
# MAIN EXTRACTOR
# ------------------------------------------------------------
def extract_raw_text(xhtml_path: str) -> str:
    """
    Fully robust XHTML/iXBRL extractor:

    1. Load raw XHTML
    2. Parse DOM with BeautifulSoup (lxml)
    3. Remove scripts, styles, metadata
    4. Walk through the document in order and collect:
       - Headings (h1-h6) as lines prefixed with "### "
       - Narrative text blocks as paragraphs
    5. Clean each line
    6. Return clean text with blank lines between blocks
    """
    raw = Path(xhtml_path).read_text(encoding="utf-8", errors="ignore")

    # Parse XHTML
    try:
        soup = BeautifulSoup(raw, "lxml")
    except Exception:
        soup = BeautifulSoup(raw, "xml")

    # Remove garbage tags that never contain narrative
    for tag in soup(["script", "style", "meta", "link", "head", "title"]):
        tag.decompose()

    body = soup.body or soup  # fallback if <body> missing

    blocks = []

    # Iterate through relevant tags in document order
    # BeautifulSoup's find_all preserves order.
    for node in body.find_all(True):
        if not isinstance(node, Tag):
            continue

        name = node.name.lower()

        is_heading = name in HEADING_TAGS
        is_block = name in BLOCK_TAGS

        if not (is_heading or is_block):
            continue

        # Avoid double-collecting: if a div/section is just a wrapper
        # around other block elements, skip it.
        if name in ["div", "section", "article", "span"]:
            has_block_children = any(
                isinstance(child, Tag)
                and (child.name.lower() in BLOCK_TAGS or child.name.lower() in HEADING_TAGS)
                for child in node.children
            )
            if has_block_children:
                continue

        text = node.get_text(" ", strip=True)
        if not text:
            continue

        cleaned = clean_line(text, is_heading=is_heading)
        if not cleaned:
            continue

        # Mark headings explicitly so LLM can use them as boundaries
        if is_heading:
            blocks.append(f"### {cleaned}")
        else:
            blocks.append(cleaned)

    # Merge adjacent identical lines (simple dedupe)
    merged_blocks = []
    last = None
    for b in blocks:
        if b != last:
            merged_blocks.append(b)
        last = b

    # Join paragraphs with blank lines between them
    result = "\n\n".join(merged_blocks).strip()

    return result

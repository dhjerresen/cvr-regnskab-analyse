# xhtml_extractor.py
"""
Extracts structured narrative content from XHTML/iXBRL files.
"""

from bs4 import BeautifulSoup
from pathlib import Path

HEADING_TAGS = ["h1", "h2", "h3", "h4"]


def is_heading(element):
    """Heuristic: detect headings that are not proper <h1>-<h4>."""
    txt = element.get_text(" ", strip=True)
    if not txt or len(txt) > 200:
        return False

    # Fully bold?
    if element.find("strong") or element.find("b"):
        return True

    # CSS-based headings (common in Vestas)
    style = element.get("style", "").lower()
    if "font-size" in style and ("18" in style or "20" in style or "24" in style):
        return True
    if "font-weight" in style and ("600" in style or "700" in style):
        return True

    # All caps (ACRONYMS ignored)
    if txt.isupper() and txt.isalpha() and len(txt) > 3:
        return True

    return False


def extract_sections(xhtml_path: str) -> list[dict]:
    soup = BeautifulSoup(Path(xhtml_path).read_text(encoding="utf-8"), "lxml")

    sections = []
    current_title = None
    current_text = []

    for el in soup.find_all(True):
        tag = el.name.lower()

        # True heading
        if tag in HEADING_TAGS or is_heading(el):
            # Finalize previous section
            if current_title or current_text:
                sections.append({
                    "title": current_title,
                    "text": "\n".join(current_text).strip()
                })
            current_title = el.get_text(" ", strip=True)
            current_text = []
            continue

        # Collect narrative text
        if tag in ["p", "div", "span", "section"]:
            txt = el.get_text(" ", strip=True)
            if txt:
                current_text.append(txt)

    # Final section
    if current_title or current_text:
        sections.append({
            "title": current_title,
            "text": "\n".join(current_text).strip()
        })

    return sections
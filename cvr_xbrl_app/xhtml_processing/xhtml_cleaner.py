# xhtml_cleaner.py
"""
Utility for cleaning and shrinking large XHTML/iXBRL reports by
removing images, inline base64 content, and unnecessary heavy tags.

This version keeps all iXBRL tags intact for Arelle/NLP processing.
"""

from bs4 import BeautifulSoup
from pathlib import Path
import re


def remove_images_and_base64(xhtml_path: str, output_path: str | None = None) -> str:
    """
    Removes <img> tags and inline base64 images from an XHTML file.
    Dramatically reduces file size (70MB → ~3MB).

    Args:
        xhtml_path (str): Path to input XHTML file.
        output_path (str, optional): Path to save cleaned file.
                                     If None → creates '{name}_clean.xhtml'.

    Returns:
        str: Path to cleaned XHTML.
    """
    xhtml_path = Path(xhtml_path)
    content = xhtml_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "lxml")

    # Remove all <img> tags
    for img in soup.find_all("img"):
        img.decompose()

    # Remove inline base64 images
    cleaned = re.sub(
        r"data:image\/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+",
        "",
        str(soup)
    )

    # Save output
    if output_path is None:
        output_path = str(xhtml_path.with_name(xhtml_path.stem + "_clean.xhtml"))

    Path(output_path).write_text(cleaned, encoding="utf-8")
    return output_path

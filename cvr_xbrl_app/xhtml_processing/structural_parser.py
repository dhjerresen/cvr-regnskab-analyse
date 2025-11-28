# structural_parser.py
"""
Optional: Build a nested hierarchical structure (tree)
where h1 contains h2 contains h3 etc.
"""

from bs4 import BeautifulSoup
from pathlib import Path

HEADING_ORDER = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}


def parse_structure(xhtml_path: str) -> list:
    """
    Returns a tree-like structure for the XHTML document.

    Example:
    [
        {
            "title": "Management Review",
            "level": 1,
            "children": [
                {
                    "title": "Strategy",
                    "level": 2,
                    "children": [...]
                }
            ]
        }
    ]
    """
    soup = BeautifulSoup(Path(xhtml_path).read_text(encoding="utf-8"), "lxml")

    root = []
    stack = []

    for el in soup.find_all(True):
        tag = el.name.lower()

        if tag not in HEADING_ORDER:
            continue

        level = HEADING_ORDER[tag]
        title = el.get_text(" ", strip=True)

        node = {"title": title, "level": level, "children": []}

        # Place node correctly in hierarchy
        while stack and stack[-1]["level"] >= level:
            stack.pop()

        if stack:
            stack[-1]["children"].append(node)
        else:
            root.append(node)

        stack.append(node)

    return root

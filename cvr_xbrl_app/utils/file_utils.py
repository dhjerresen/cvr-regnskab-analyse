"""
file_utils.py
--------------
Utility functions for handling temporary files, safe downloads,
and simple caching if needed.
"""

import tempfile
import requests
from pathlib import Path


def download_to_temp(url: str, suffix: str = "") -> str:
    """
    Downloads a file to a NamedTemporaryFile and returns the file path.

    Args:
        url (str): URL to download.
        suffix (str): File extension, e.g., '.xhtml', '.xml'

    Returns:
        str: Path to temporary downloaded file.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    response = requests.get(url, timeout=15)
    tmp.write(response.content)
    tmp.flush()
    return tmp.name


def save_text_to_file(text: str, filename: str) -> str:
    """
    Saves text to a local file. Mainly useful for debugging.
    """
    path = Path(filename)
    path.write_text(text, encoding="utf-8")
    return str(path)

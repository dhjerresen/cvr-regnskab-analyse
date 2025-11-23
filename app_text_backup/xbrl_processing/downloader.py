"""
downloader.py
--------------
Utility module for downloading XBRL or PDF files
from official Erhvervsstyrelsen publication URLs.
"""

import requests

def download_xbrl(url: str, save_path: str) -> str:
    """
    Downloader en XBRL-fil fra en given URL og gemmer den lokalt.

    Args:
        url (str): Download-URL til dokumentet (fra Erhvervsstyrelsens API).
        save_path (str): Sti, hvor filen skal gemmes (inkl. filnavn).

    Returns:
        str: Den lokale sti til den gemte fil.
    """
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(resp.content)

        return save_path

    except requests.RequestException as e:
        print(f"[Fejl] Kunne ikke downloade XBRL-fil: {e}")
        raise
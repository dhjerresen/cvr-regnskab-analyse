# xbrl_processing/downloader.py
import requests

def download_xbrl(url: str, save_path: str) -> str:
    """
    Download an XBRL/iXBRL file and save to disk.
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

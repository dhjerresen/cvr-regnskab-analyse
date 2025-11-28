# xbrl_processing/instance_finder.py

import tempfile
import zipfile
import requests
import io
import os

from xbrl_processing.downloader import download_xbrl


# ------------------------------------------
# Helper: detect inline XBRL
# ------------------------------------------
def file_contains_ixbrl(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return (
        "<ix:" in t or 
        "<ix:non" in t or 
        "<ix:header" in t or
        "xmlns:ix" in t
    )


# ------------------------------------------
# Helper: detect normal XBRL XML
# ------------------------------------------
def file_contains_xbrl_xml(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return (
        "<xbrli:" in t or 
        "xmlns:xbrli" in t or 
        "http://www.xbrl.org" in t
    )


# ------------------------------------------
# Detect correct ESEF XHTML inside ZIP
# ------------------------------------------
def find_esef_xhtml_in_zip(url: str):
    try:
        resp = requests.get(url, timeout=15)
        z = zipfile.ZipFile(io.BytesIO(resp.content))

        # List XHTML/HTML files only
        candidates = [
            name for name in z.namelist()
            if name.lower().endswith((".xhtml", ".html"))
        ]
        if not candidates:
            return None, None

        # Priority 1: look for inline XBRL markup in file content
        for name in candidates:
            try:
                content = z.read(name).decode("utf-8", errors="ignore")
                if file_contains_ixbrl(content):
                    return z, name
            except:
                pass

        # Priority 2: common ESEF names
        for name in candidates:
            if "report" in name.lower():
                return z, name
            if "xbrl" in name.lower():
                return z, name

        # Priority 3: fallback to largest XHTML file
        largest = max(candidates, key=lambda n: len(z.read(n)))
        return z, largest

    except Exception:
        return None, None


# ------------------------------------------
# MAIN ENTRY POINT DETECTOR
# ------------------------------------------
def find_valid_instance(df):
    """
    Returns a local filepath to a valid XBRL/iXBRL instance file.
    Handles:
      - IFRS/ESEF XHTML (inside ZIP)
      - ÅRL XML
    """

    # ===============================
    # 1) Try ZIP → XHTML (ESEF)
    # ===============================
    zip_rows = df[df["Url"].str.contains(".zip", case=False, na=False)]

    if not zip_rows.empty:
        for _, row in zip_rows.iterrows():
            zfile, entry = find_esef_xhtml_in_zip(row["Url"])
            if entry:
                with tempfile.NamedTemporaryFile(suffix=".xhtml", delete=False) as tmp:
                    tmp.write(zfile.read(entry))
                    tmp.flush()
                    return tmp.name  # FOUND XHTML instance


    # ===============================
    # 2) Try XML (ÅRL)
    # ===============================
    xml_rows = df[
        df["Url"].str.contains(".xml", case=False, na=False) |
        df["Filtype"].str.contains("XBRL", case=False, na=False) |
        df["Url"].str.contains("xbrl", case=False, na=False)
    ]

    if not xml_rows.empty:
        for _, row in xml_rows.iterrows():
            try:
                resp = requests.get(row["Url"], timeout=10)
                chunk = resp.content[:200000].decode("utf-8", errors="ignore")

                if file_contains_xbrl_xml(chunk):
                    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
                        download_xbrl(row["Url"], tmp.name)
                        return tmp.name  # FOUND XML instance

            except Exception:
                pass

    # ===============================
    # NOTHING FOUND
    # ===============================
    return None

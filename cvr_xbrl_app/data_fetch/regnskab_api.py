# data_fetch/regnskab_api.py

import requests
from datetime import datetime

def classify_filetype(mime: str, url: str) -> str:
    url_low = url.lower().split("?", 1)[0]

    if mime == "application/pdf" or url_low.endswith(".pdf"):
        return "PDF"

    if mime in ("application/xhtml+xml", "text/html") or url_low.endswith((".xhtml", ".html", ".htm")):
        return "iXBRL"

    if mime in ("application/xml", "text/xml") or url_low.endswith(".xml"):
        return "XBRL"

    return "XBRL"


def is_annual_report(period):
    start = period.get("startDato")
    end = period.get("slutDato")
    if not start or not end:
        return False
    try:
        d1 = datetime.fromisoformat(start[:10])
        d2 = datetime.fromisoformat(end[:10])
    except:
        return False

    days = (d2 - d1).days
    return 350 <= days <= 380


def hent_regnskaber(cvr: int) -> list[dict]:
    base_url = "http://distribution.virk.dk/offentliggoerelser/_search"
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"cvrNummer": cvr}},
                    {"term": {"offentliggoerelsestype": "regnskab"}}
                ]
            }
        },
        "_source": [
            "dokumenter",
            "regnskab.regnskabsperiode",
            "offentliggoerelsesTidspunkt"
        ],
        "sort": [{"offentliggoerelsesTidspunkt": {"order": "desc"}}],
        "size": 40
    }

    try:
        resp = requests.post(base_url, json=query, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return []

        regnskaber = []
        for hit in hits:
            src = hit.get("_source", {})
            periode = src.get("regnskab", {}).get("regnskabsperiode", {})

            # --- FILTER: ONLY ANNUAL REPORTS ---
            if not is_annual_report(periode):
                continue

            offentliggjort = src.get("offentliggoerelsesTidspunkt", "")
            dokumenter = src.get("dokumenter", [])

            for d in dokumenter:
                mime = d.get("dokumentMimeType", "")
                url = d.get("dokumentUrl", "")
                description = d.get("dokumentType", "")
                filetype = classify_filetype(mime, url)

                regnskaber.append({
                    "Startdato": periode.get("startDato"),
                    "Slutdato": periode.get("slutDato"),
                    "Offentliggjort": offentliggjort,
                    "Filtype": filetype,
                    "Url": url,
                    "Beskrivelse": description,
                })

        # Sort by end date (newest first)
        regnskaber.sort(key=lambda r: r["Slutdato"], reverse=True)
        return regnskaber

    except requests.RequestException as e:
        print(f"[Fejl] Kunne ikke hente regnskaber: {e}")
        return []

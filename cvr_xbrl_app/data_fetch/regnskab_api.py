# data_fetch/regnskab_api.py

import requests

def classify_filetype(mime: str, url: str) -> str:
    """
    PDF, iXBRL, XBRL classification.
    No ZIP logic (not needed).
    """
    url_low = url.lower().split("?", 1)[0]

    if mime == "application/pdf" or url_low.endswith(".pdf"):
        return "PDF"

    if mime in ("application/xhtml+xml", "text/html") or url_low.endswith((".xhtml", ".html", ".htm")):
        return "iXBRL"

    if mime in ("application/xml", "text/xml") or url_low.endswith(".xml"):
        return "XBRL"

    return "XBRL"


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
            offentliggjort = src.get("offentliggoerelsesTidspunkt", "")
            dokumenter = src.get("dokumenter", [])

            for d in dokumenter:
                mime = d.get("dokumentMimeType", "")
                url = d.get("dokumentUrl", "")
                filetype = classify_filetype(mime, url)

                regnskaber.append({
                    "Startdato": periode.get("startDato"),
                    "Slutdato": periode.get("slutDato"),
                    "Offentliggjort": offentliggjort,
                    "Filtype": filetype,
                    "Url": url,
                })

        return regnskaber

    except requests.RequestException as e:
        print(f"[Fejl] Kunne ikke hente regnskaber: {e}")
        return []

"""
regnskab_api.py
---------------
Module for fetching Danish company annual report metadata
from Erhvervsstyrelsens 'distribution.virk.dk' API.
"""

import requests

def hent_regnskaber(cvr: int) -> list[dict]:
    """
    Henter årsrapporter (PDF/XBRL) for en given virksomhed ud fra CVR-nummer.

    Args:
        cvr (int): CVR-nummer på virksomheden.

    Returns:
        list[dict]: En liste med årsrapporter, hver med start/slutdato, offentliggørelse og download-URL.
    """
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
        "size": 20
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
            offentliggoerelsesdato = src.get("offentliggoerelsesTidspunkt", "")
            dokumenter = src.get("dokumenter", [])

            for d in dokumenter:
                mime = d.get("dokumentMimeType", "")
                regnskaber.append({
                    "Startdato": periode.get("startDato"),
                    "Slutdato": periode.get("slutDato"),
                    "Offentliggjort": offentliggoerelsesdato,
                    "Filtype": "PDF" if mime == "application/pdf" else "XBRL",
                    "Url": d.get("dokumentUrl")
                })

        return regnskaber

    except requests.RequestException as e:
        print(f"[Fejl] Kunne ikke hente regnskaber fra Erhvervsstyrelsen: {e}")
        return []
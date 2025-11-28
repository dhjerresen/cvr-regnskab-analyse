"""
cvr_api.py
----------
Module for fetching basic company information from the public CVR API (cvrapi.dk).
"""

import json
import contextlib
import urllib.request as request


# --- Helper: Determine company status from CVR API fields ---
def _derive_status(data: dict) -> str:
    """
    Computes a clean human-readable company status based on CVR API fields.

    Logic:
        - If creditbankrupt == true  -> "Konkurs"
        - Else if enddate exists     -> "Ophørt"
        - Else                       -> "Aktiv"
    """

    if data.get("creditbankrupt"):
        return "Konkurs"

    if data.get("enddate"):
        return "Ophørt"

    return "Aktiv"


# --- Main function ---
def hent_cvr_data(cvr: int, country: str = "dk") -> dict:
    """
    Henter virksomhedsdata fra CVR API'et (cvrapi.dk).

    Args:
        cvr (int): CVR-nummer for virksomheden.
        country (str): Landekode (default = 'dk').

    Returns:
        dict: Dictionary med originale CVR-data + tilføjet felt 'status'.
    """
    try:
        req = request.Request(
            url=f"https://cvrapi.dk/api?search={cvr}&country={country}",
            headers={
                "User-Agent": (
                    "Hjerresen Multiservice - MVP CVR lookup "
                    "- Kontakt: danielhjerresen@hotmail.dk"
                )
            },
        )

        with contextlib.closing(request.urlopen(req)) as response:
            data = json.loads(response.read())

        # --- Add derived status field ---
        data["status"] = _derive_status(data)

        # --- Make sure missing fields return None instead of crashing UI ---
        safe_fields = {
            "name": None,
            "address": None,
            "zipcode": None,
            "city": None,
            "industrydesc": None,
            "startdate": None,
        }

        for key in safe_fields:
            data.setdefault(key, safe_fields[key])

        return data

    except Exception as e:
        print(f"[Fejl] Kunne ikke hente CVR-data: {e}")
        return None

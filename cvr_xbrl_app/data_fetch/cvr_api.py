"""
cvr_api.py
----------
Module for fetching basic company information from the public CVR API (cvrapi.dk).
"""

import json
import contextlib
import urllib.request as request

# --- Main function ---
def hent_cvr_data(cvr: int, country: str = "dk") -> dict:
    """
    Henter virksomhedsdata fra CVR API'et (cvrapi.dk).

    Args:
        cvr (int): CVR-nummer for virksomheden.
        country (str): Landekode (default = 'dk').

    Returns:
        dict: Et dictionary med virksomhedsdata, eller None hvis der opstod en fejl.
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
            return data

    except Exception as e:
        print(f"[Fejl] Kunne ikke hente CVR-data: {e}")
        return None

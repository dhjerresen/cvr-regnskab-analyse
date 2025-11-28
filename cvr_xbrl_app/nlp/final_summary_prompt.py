# nlp/final_summary_prompt.py

"""
Creates one unified LLM prompt combining:

- XBRL general analysis
- XBRL financial data
- Ledelsesberetning (raw text)

No formatting or logic is stored in app.py.
"""

from utils.formatting import dk_number, dk_percent

def build_final_summary_prompt(xbrl_general, xbrl_financial, ledelsesberetning_raw):
    """
    Build the full LLM prompt used for the final combined summary.
    The prompt is intentionally deterministic, structured and neutral.
    """

    # --------- GENERAL XBRL FIELDS ----------
    aktivitet = xbrl_general.get("Væsentlig aktivitet", "Ingen oplysning")
    klass = xbrl_general.get("Anvendt regnskabsklasse", "Ingen oplysning")
    erkl = xbrl_general.get("Revisionstype", "Ingen oplysning")
    revisor = xbrl_general.get("Revisortype", "Ingen oplysning")

    fejl = xbrl_general.get("Korrektion af væsentlig fejl")
    going = xbrl_general.get("Going concern usikkerhed")

    if not fejl and not going:
        bemaerkning = (
            "Erklæringsgiver har ingen bemærkninger vedrørende væsentlige fejl "
            "eller usikkerhed om going concern."
        )
    else:
        parts = []
        if fejl:
            parts.append(f"Bemærkning om væsentlig fejl: {fejl}.")
        if going:
            parts.append(f"Bemærkning om going concern: {going}.")
        bemaerkning = " ".join(parts)

    # ---------- FINANCIAL DATA ----------
    years = xbrl_financial.get("Years", {})
    cy = years.get("CY", "")
    py = years.get("PY", "")

    indtjening = xbrl_financial.get("Indtjening", {})
    balance = xbrl_financial.get("Balance", {})
    nøgletal = xbrl_financial.get("Nøgletal", {})

    res_cy = dk_number(indtjening.get("Årets resultat", {}).get("CY"))
    res_py = dk_number(indtjening.get("Årets resultat", {}).get("PY"))

    eq_cy = dk_number(balance.get("Egenkapital", {}).get("CY"))
    eq_py = dk_number(balance.get("Egenkapital", {}).get("PY"))

    sg_cy = nøgletal.get("Soliditetsgrad", {}).get("CY")
    sg_py = nøgletal.get("Soliditetsgrad", {}).get("PY")
    sg_cy_f = dk_percent(sg_cy)
    sg_py_f = dk_percent(sg_py)

    gg_cy = nøgletal.get("Gældsgrad", {}).get("CY")
    gg_py = nøgletal.get("Gældsgrad", {}).get("PY")
    gg_cy_f = dk_percent(gg_cy)
    gg_py_f = dk_percent(gg_py)

    # ---------- PROMPT ----------
    return f"""
Du er en professionel økonom, der skriver en samlet dansk regnskabsmæssig sammenfatning.

BRUG KUN DATA, der står herunder — ingen gæt, ingen antagelser.

============================================
DATADEL 1 — XBRL: GENEREL INFORMATION
============================================
Aktivitet: {aktivitet}
Regnskabsklasse: {klass}
Erklæringstype: {erkl}
Revisortype: {revisor}
Bemærkninger: {bemaerkning}

============================================
DATADEL 2 — XBRL: FINANSIELLE DATA
============================================
Indtjeningsudvikling (Årets resultat): {res_py} → {res_cy}
Egenkapital: {eq_py} → {eq_cy}
Soliditetsgrad: {sg_py_f} → {sg_cy_f}
Gældsgrad: {gg_py_f} → {gg_cy_f}

============================================
DATADEL 3 — LEDELSESBERETNING (råtekst)
============================================
{ledelsesberetning_raw}

============================================
OPGAVE
============================================

Skriv en struktureret, klar og neutral sammenfatning, opdelt i disse afsnit:

1) Virksomhedens aktivitet, regnskabsklasse, revisorforhold og bemærkninger  
2) Udviklingen i de centrale økonomiske nøgletal  
3) De vigtigste pointer fra ledelsesberetningen  
4) En samlet konklusion om virksomhedens økonomiske situation

Ingen gæt, ingen eksterne oplysninger. Kun data ovenfor.

Start nu.
"""
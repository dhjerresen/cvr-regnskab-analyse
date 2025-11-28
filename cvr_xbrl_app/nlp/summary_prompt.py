# summary_prompt.py

def dk(x):
    """ Dansk tusindtalsformat uden decimaler. """
    if x is None or isinstance(x, str):
        return x
    return f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_summary_prompt(general, financial):
    aktivitet = general.get("Væsentlig aktivitet", "Ingen oplysning")
    klass = general.get("Anvendt regnskabsklasse", "Ingen oplysning")
    erkl = general.get("Revisionstype", "Ingen oplysning")
    revisor = general.get("Revisortype", "Ingen oplysning")

    fejl = general.get("Korrektion af væsentlig fejl")
    going = general.get("Going concern usikkerhed")

    # Bemærkningstekst genereres 100% deterministisk
    if (not fejl and not going):
        bemaerkning = "Erklæringsgiver har ingen bemærkninger vedrørende væsentlige fejl eller usikkerhed om going concern."
    else:
        parts = []
        if fejl:
            parts.append(f"Bemærkning om væsentlig fejl: {fejl}.")
        if going:
            parts.append(f"Bemærkning om going concern: {going}.")
        bemaerkning = "Erklæringsgiver har følgende bemærkninger: " + " ".join(parts)

    # Finansielle tal – pænt formaterede
    cy = financial["Years"].get("CY")
    py = financial["Years"].get("PY")

    res_cy = dk(financial["Indtjening"]["Årets resultat"]["CY"])
    res_py = dk(financial["Indtjening"]["Årets resultat"]["PY"])

    eq_cy = dk(financial["Balance"]["Egenkapital"]["CY"])
    eq_py = dk(financial["Balance"]["Egenkapital"]["PY"])

    sg_cy = financial["Nøgletal"]["Soliditetsgrad"]["CY"]
    sg_py = financial["Nøgletal"]["Soliditetsgrad"]["PY"]
    sg_cy_f = f"{sg_cy:.2f}" if sg_cy else "0"
    sg_py_f = f"{sg_py:.2f}" if sg_py else "0"

    gg_cy = financial["Nøgletal"]["Gældsgrad"]["CY"]
    gg_py = financial["Nøgletal"]["Gældsgrad"]["PY"]
    gg_cy_f = f"{gg_cy:.2f}" if gg_cy else "0"
    gg_py_f = f"{gg_py:.2f}" if gg_py else "0"

    return f"""
Du skal skrive en kort, faktuel opsummering på dansk, med PRÆCIS denne struktur:

---------------------
AFSNIT 1 (1–3 linjer, ingen overskrift til afsnittet)
---------------------
Skriv i én samlet paragraf:
- selskabets hovedaktivitet
- hvilken regnskabsklasse årsrapporten er aflagt efter
- erklæringstype
- revisortype
- bemærkninger (brug teksten FRA DATA – ikke dine egne ord)

TEKST TIL AFSNIT 1:
Aktivitet: {aktivitet}
Regnskabsklasse: {klass}
Erklæringstype: {erkl}
Revisortype: {revisor}
Bemærkninger: {bemaerkning}

---------------------
AFSNIT 2 (nyt afsnit, 3–5 linjer, ingen overskrift til afsnittet)
---------------------
Beskriv KUN udviklingen i:
- årets resultat
- egenkapital
- soliditetsgrad
- gældsgrad

Ingen fortolkning, ingen årsager, ingen subjektive ord.
Kort og præcist.

FINANSTAL:
Årets resultat: {res_py} → {res_cy}
Egenkapital: {eq_py} → {eq_cy}
Soliditetsgrad: {sg_py_f} → {sg_cy_f}
Gældsgrad: {gg_py_f} → {gg_cy_f}

Start nu.
"""
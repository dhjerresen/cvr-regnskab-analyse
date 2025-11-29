# summary_prompt.py
import json

def build_summary_prompt(xbrl_json: dict):
    json_text = json.dumps(xbrl_json, ensure_ascii=False, indent=2)

    return f"""
Du får her strukturerede XBRL-data fra en årsrapport i JSON-format.

OPGAVE:
Skriv en kort, præcis og faglig årsrapport-sammenfatning bestående af to afsnit:
1) Et kvalitativt afsnit som én sammenhængende paragraf.
2) Et finansielt afsnit som én sammenhængende paragraf med 4–6 sætninger.

VIGTIGE FORMATKRAV:
- Brug KUN oplysninger fra JSON.
- Hvis en værdi mangler eller er null → “ikke rapporteret”.
- Alle tal skal skrives uden decimaler (fx 1.234.567 og ikke 1.234.567,00).
- Angiv valuta kun én gang i det finansielle afsnit (efter første talblok).
- Brug dansk tusindtalsformat med punktum.
- Brug periodens label fra JSON (fx “2024/25” eller “2024”).
- Undgå sætninger hvor både CY og PY er “ikke rapporteret”.
- Ingen punktlister, ingen overskrifter, ingen emojis.

AFSNIT 1 — KVALITATIVT  
Skriv 3–5 linjer om:
- hovedaktivitet  
- regnskabsklasse  
- erklæringstype og revisortype  
- eventuelle bemærkninger om going concern og væsentlige fejl  
Afsnittet skal være én samlet paragraf.

AFSNIT 2 — FINANSIEL UDVIKLING  
Skriv 4–6 sammenhængende sætninger om udviklingen i:
- bruttofortjeneste  
- driftsresultat  
- årets resultat  
- egenkapital  
- et centralt nøgletal (fx soliditetsgrad)  
Brug formuleringer som: “Bruttofortjenesten steg fra X til Y i perioden LABEL”.  
Valuta skrives kun én gang i afsnittet, typisk efter den første sætning.

Her er JSON-data:
```json
{json_text}
"""
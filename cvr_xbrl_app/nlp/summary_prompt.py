# summary_prompt.py
import json

def build_summary_prompt(xbrl_json: dict):
    json_text = json.dumps(xbrl_json, ensure_ascii=False, indent=2)

    return f"""
Du får her strukturerede XBRL-data fra en årsrapport i JSON-format. Du skal skrive en kort, faglig og præcis sammenfatning opdelt i to afsnit: et kvalitativt afsnit og et finansielt afsnit. Outputtet skal være i præcis samme stil og struktur som eksemplet nedenfor.

────────────────────────────────────────
EKSEMPEL PÅ STIL, STRUKTUR OG LÆNGDE  
(Du skal efterligne dette 1:1 i tone, format, længde og opbygning)

Selskabets væsentlige aktiviteter består af at drive VVS-virksomhed. Årsrapporten for perioden 2024/25 er aflagt efter regnskabsklasse B og er forsynet med en udvidet gennemgang udført af en registreret revisor. Der er ingen bemærkninger vedrørende going concern eller væsentlige fejl.

Bruttofortjenesten er steget fra 9.023.590 til 10.574.310 i perioden 2024/25. Driftsresultatet steg fra 1.106.268 til 1.216.244. Årets resultat forbedredes fra 919.324 til 947.982. Egenkapitalen voksede fra 2.039.513 til 2.087.495. Soliditetsgraden steg fra 43,83 % til 44,71 %.
────────────────────────────────────────

DU SKAL FØLGE DISSE KRAV:

GENERELLE REGLER
- Brug KUN oplysninger fra JSON. Ingen antagelser.
- Hvis en værdi mangler → skriv “ikke rapporteret”.
- Output skal bestå af PRÆCIS TO sammenhængende afsnit i prosa.
- INGEN punktopstillinger, INGEN overskrifter, INGEN emojis.

SPROG OG FORMATERING
- Brug dansk tusindtalsformat med punktum (fx 1.234.567).
- Tal må ikke have decimaler (ingen “,00”).
- Valuta (fx DKK) nævnes kun én gang i finans-afsnittet.
- Anvend periodens 'label' fra JSON (fx “2024/25” eller “2024”).
- Undgå at skrive sætninger hvor både CY og PY er “ikke rapporteret”.
- Skriv kort, fagligt og nøgternt – samme stil som eksemplet.

AFSNIT 1 — KVALITATIVT (én paragraf)
Skriv 3–5 linjer der beskriver:
- Hovedaktivitet  
- Regnskabsklasse  
- Erklæringstype og revisortype  
- Eventuelle bemærkninger om going concern eller væsentlige fejl  
Brug samme tone og rytme som i eksemplet.

AFSNIT 2 — FINANSIEL UDVIKLING (én paragraf)
Skriv 4–6 sætninger der beskriver udviklingen i:
- Bruttofortjeneste  
- Driftsresultat  
- Årets resultat  
- Egenkapital  
- Ét centralt nøgletal (fx soliditetsgrad eller overskudsgrad)  
Brug periodens label i stil med: “i perioden 2024/25”.  
Valuta angives kun i første sætning.  
Sætningerne skal følge samme stil som i eksemplet.

────────────────────────────────────────
HER ER JSON-DATA:
```json
{json_text}

"""
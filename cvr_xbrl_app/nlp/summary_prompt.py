# summary_prompt.py
import json

def build_summary_prompt(xbrl_json: dict):
    json_text = json.dumps(xbrl_json, ensure_ascii=False, indent=2)

    return f"""
Du får her strukturerede XBRL-data fra en årsrapport i JSON-format.

FØLG DISSE REGLER:
- Brug KUN de tal og oplysninger, der findes i JSON.
- Hvis en værdi er null, skriv “ikke rapporteret”.
- Lav ingen gæt eller antagelser.
- Brug valutaen præcis som den fremgår af JSON.
- Angiv alle beløb i dansk tusindtalsformat.
- Brug danske fagudtryk.

Her er JSON-data:
```json
{json_text}"""
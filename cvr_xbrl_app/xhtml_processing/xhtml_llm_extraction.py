"""
xhtml_llm_extraction.py
-----------------------
LLM-based extraction of Ledelsesberetning / Management Review.

This module assumes you already called:

    raw_text = extract_raw_text(xhtml_path)

where `raw_text` contains headings like:

    ### Ledelsesberetning
    ### Koncernledelsesberetning
"""

from typing import Callable
from .xhtml_chunker import chunk_text

SYSTEM_PROMPT = """
Du er en ekspert i danske årsrapporter og i særdeleshed i at finde afsnittet
'Ledelsesberetning' / 'Management Review'.

Din opgave:
- Udtræk præcis den tekst, der tilhører Ledelsesberetningen.
- Du arbejder på tekst, hvor overskrifter er markeret sådan: '### Overskrift'.
- Typiske relevante overskrifter:
  * Ledelsesberetning
  * Koncernledelsesberetning
  * Brev til aktionærer
  * Udvikling i aktiviteter og økonomiske forhold
  * Væsentlige begivenheder
  * Usikkerheder og risici
  * Forventninger til fremtiden

REGLER:
- Hvis en overskrift i denne bid (chunk) tydeligt markerer start på
  Ledelsesberetningen, så skal teksten efter denne overskrift medtages,
  indtil en ny overskrift klart indikerer et andet afsnit (fx
  'Ledelsespåtegning', 'Revisionspåtegning', 'Noter' mv.).
- Hvis bidet ikke indeholder en overskrift, skal du vurdere, om teksten
  sandsynligvis er en fortsættelse af Ledelsesberetningen (fx omtale af
  aktiviteter, økonomisk udvikling, risici, forventninger).
- Returnér KUN tekst, som du vurderer er en del af Ledelsesberetningen.
- Skriv ingen forklaringer, ingen markdown, ingen metadata: KUN ren tekst.
- Hvis der absolut intet relevant er, returnér en tom streng.
"""


def _clean_llm_answer(answer: str) -> str:
    """
    Remove obvious wrapper formatting from the LLM answer
    (e.g. code fences, 'Svar:' etc.).
    """
    if not answer:
        return ""

    text = answer.strip()

    # Remove simple code fences if present
    if text.startswith("```"):
        # strip first and last fence
        parts = text.split("```")
        # keep the largest non-empty part
        candidates = [p.strip() for p in parts if p.strip()]
        if candidates:
            text = max(candidates, key=len)

    # Remove trivial labels like "Udtrukket tekst:" at the beginning
    text = text.lstrip("#").strip()
    for prefix in ["Svar:", "Tekst:", "Udtrukket tekst:", "Extracted text:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    return text


def llm_extract_ledelsesberetning(raw_text: str, run_llm_fn: Callable[[str], str]) -> str:
    """
    Split the full extracted XHTML text into chunks and use an LLM
    to extract relevant parts of the Ledelsesberetning.

    Parameters
    ----------
    raw_text : str
        Full plain-text representation of the XHTML/iXBRL document
        from extract_raw_text().
    run_llm_fn : Callable[[str], str]
        A function that sends a prompt to an LLM and returns the answer
        as a plain string. In your app this is `run_ai_model`.

    Returns
    -------
    str
        Concatenated extracted text belonging to the Ledelsesberetning.
    """
    if not raw_text:
        return ""

    # Larger chunks to give the LLM more context
    chunks = chunk_text(raw_text, max_chars=9000)
    results = []

    print("Number of chunks:", len(chunks))

    for idx, chunk in enumerate(chunks):
        user_prompt = f"""
Du modtager nu et udsnit (en bid) af en dansk årsrapport i ren tekst.

Teksten kan indeholde overskrifter markeret som:
    ### Ledelsesberetning
    ### Koncernledelsesberetning
    osv.

OPGAVE:
- Udtræk AL tekst i dette udsnit, som tilhører Ledelsesberetningen /
  Management Review.
- Medtag også tekst, der meget sandsynligt er en fortsættelse heraf.
- Returnér KUN selve teksten uden forklaring, markdown eller andre kommentarer.
- Hvis intet er relevant i denne bid, returnér en tom streng.

HER ER UDSNITTET:
\"\"\"{chunk}\"\"\"
"""

        try:
            answer = run_llm_fn(SYSTEM_PROMPT + "\n" + user_prompt)
        except Exception as e:
            print(f"[LLM ERROR chunk {idx}] {e}")
            continue

        cleaned = _clean_llm_answer(answer)
        if not cleaned:
            continue

        # Ignore obvious "no content" messages if model uses them
        lowered = cleaned.strip().lower()
        if lowered in ("", "none", "ingen", "no relevant content"):
            continue

        results.append(cleaned)

    # Join all extracted pieces with blank lines
    full = "\n\n".join(results).strip()

    # Optional simple dedupe of repeated paragraphs
    if not full:
        return ""

    lines = [ln.strip() for ln in full.splitlines() if ln.strip()]
    deduped_lines = []
    seen = set()
    for ln in lines:
        if ln in seen:
            continue
        seen.add(ln)
        deduped_lines.append(ln)

    return "\n\n".join(deduped_lines).strip()

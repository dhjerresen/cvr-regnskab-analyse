"""
xhtml_llm_summary.py
--------------------
LLM-based summarization of Ledelsesberetning.
"""

from typing import Callable

def llm_summarize_ledelsesberetning(text: str, run_llm_fn: Callable[[str], str]) -> str:

    if not text.strip():
        return "Ingen ledelsesberetning fundet."

    prompt = f"""
Du er en ekspertanalytiker.

Opsummer følgende ledelsesberetning i punkter med fokus på:
- Strategi og forretningsudvikling
- Markedsforhold
- Risici
- Årets vigtigste resultater
- Bæredygtighed/ESG (hvis nævnt)
- Fremtidsforventninger
- Direktionens og bestyrelsens nøglebudskaber

TEKST:
{text}
"""

    try:
        return run_llm_fn(prompt)
    except:
        return "Fejl: LLM kunne ikke opsummere teksten."

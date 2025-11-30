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

    Opsummer følgende ledelsesberetning i **kun tre hovedpunkter**:
    - Identificér de **3 vigtigste temaer** i hele teksten (fx strategi, resultater, risici, fusioner, markedsforhold m.m.)
    - Giv en **kort og præcis** punktopsummering af hvert tema
    - Undlad alt, der ikke er blandt de tre mest centrale temaer
    - Maks. 5 linjer pr. tema

    TEKST:
    {text}
    """

    try:
        return run_llm_fn(prompt)
    except:
        return "Fejl: LLM kunne ikke opsummere teksten."

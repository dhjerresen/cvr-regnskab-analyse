# xbrl_processing/json_transformer.py

from datetime import datetime

def normalize_number(value):
    """Convert numbers or 'Ukendt' → None, keep numbers as floats."""
    if value in (None, "", "Ukendt"):
        return None
    try:
        return float(value)
    except:
        return None


def make_period_label(start_date: str, end_date: str) -> str:
    """
    Creates a period label:
    - "2024" if period is 1 Jan → 31 Dec of the same year
    - "2024/25" if the period spans two years
    - Returns "ikke rapporteret" if missing or invalid
    """

    if not start_date or not end_date:
        return "ikke rapporteret"

    try:
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
    except:
        return "ikke rapporteret"

    # Case: Full calendar year
    if (
        s.year == e.year and
        s.month == 1 and s.day == 1 and
        e.month == 12 and e.day == 31
    ):
        return str(s.year)

    # Case: Spans two calendar years → e.g. 2024/25
    return f"{s.year}/{str(e.year)[-2:]}"


def transform_xbrl_to_json(general: dict, financial: dict) -> dict:
    """
    Convert your internal XBRL dicts into a stable, LLM-friendly JSON schema.
    This schema is optimized for natural-language summarization with minimal hallucination.
    """

    # ----- GENERAL SECTION -----
    gen = {
        "audit_type": general.get("Revisionstype"),
        "auditor_type": general.get("Revisortype"),
        "going_concern": general.get("Going concern usikkerhed"),
        "main_activity": general.get("Væsentlig aktivitet"),
        "material_error_correction": general.get("Korrektion af væsentlig fejl"),
        "accounting_class": general.get("Anvendt regnskabsklasse"),
        "accounting_class_upgrade": general.get("Tilvalg af højere regnskabsklasse")
    }

    # ----- PERIODS SECTION -----
    cy = financial["Years"]["CY"]
    py = financial["Years"]["PY"]

    cy_start = cy.get("start")
    cy_end   = cy.get("end")
    py_start = py.get("start")
    py_end   = py.get("end")

    periods = {
        "date_format": "YYYY-MM-DD",
        "CY": {
            "start": cy_start,
            "end": cy_end,
            "period_string": f"{cy_start} til {cy_end}",
            "label": make_period_label(cy_start, cy_end)
        },
        "PY": {
            "start": py_start,
            "end": py_end,
            "period_string": f"{py_start} til {py_end}",
            "label": make_period_label(py_start, py_end)
        }
    }

    # ----- FINANCIAL SECTION -----
    fin = {
        "currency": financial.get("Valuta"),
        "periods": periods,
        "income_statement": {},
        "balance_sheet": {},
        "ratios": {}
    }

    # ---- Income statement ----
    for label, values in financial.get("Indtjening", {}).items():
        fin["income_statement"][label] = {
            "CY": normalize_number(values.get("CY")),
            "PY": normalize_number(values.get("PY"))
        }

    # ---- Balance sheet ----
    for label, values in financial.get("Balance", {}).items():
        fin["balance_sheet"][label] = {
            "CY": normalize_number(values.get("CY")),
            "PY": normalize_number(values.get("PY"))
        }

    # ---- Ratios ----
    for label, values in financial.get("Nøgletal", {}).items():
        fin["ratios"][label] = {
            "CY": normalize_number(values.get("CY")),
            "PY": normalize_number(values.get("PY"))
        }

    # ---- FINAL RETURN STRUCTURE ----
    return {
        "general_analysis": gen,
        "financial_analysis": fin
    }

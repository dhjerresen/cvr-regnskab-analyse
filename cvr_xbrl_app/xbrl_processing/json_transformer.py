# xbrl_processing/json_transformer.py

def normalize_number(value):
    """Convert numbers or 'Ukendt' → None, keep numbers as floats."""
    if value in (None, "", "Ukendt"):
        return None
    try:
        return float(value)
    except:
        return None


def transform_xbrl_to_json(general: dict, financial: dict) -> dict:
    """
    Convert your internal XBRL dicts into a stable, LLM-friendly JSON schema.
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

    # ----- FINANCIAL SECTION -----
    fin = {
        "currency": financial.get("Valuta"),
        "periods": {
            "current_year": {
                "start_date": financial["Years"]["CY"].get("start"),
                "end_date": financial["Years"]["CY"].get("end"),
            },
            "previous_year": {
                "start_date": financial["Years"]["PY"].get("start"),
                "end_date": financial["Years"]["PY"].get("end"),
            }
        },
        "income_statement": {},
        "balance_sheet": {},
        "ratios": {}
    }

    # ---- Income statement ----
    for label, values in financial.get("Indtjening", {}).items():
        fin["income_statement"][label] = {
            "current_year": normalize_number(values.get("CY")),
            "previous_year": normalize_number(values.get("PY"))
        }

    # ---- Balance ----
    for label, values in financial.get("Balance", {}).items():
        fin["balance_sheet"][label] = {
            "current_year": normalize_number(values.get("CY")),
            "previous_year": normalize_number(values.get("PY"))
        }

    # ---- Ratios ----
    for label, values in financial.get("Nøgletal", {}).items():
        fin["ratios"][label] = {
            "current_year": normalize_number(values.get("CY")),
            "previous_year": normalize_number(values.get("PY"))
        }

    return {
        "general_analysis": gen,
        "financial_analysis": fin
    }

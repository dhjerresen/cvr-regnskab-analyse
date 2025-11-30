# xbrl_processing/financial_parser.py

"""
financial_parser.py — TWO-YEAR VERSION WITH 'UKENDT' REVENUE
------------------------------------------------------------
Extracts current year (CY) and previous year (PY) financials from
Danish XBRL/iXBRL files using Arelle.

Extended to also extract qualitative text such as
'Væsentlig aktivitet' directly from XBRL/iXBRL.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, Tuple, Dict

from .arelle_loader import load_model
from .taxonomy_map import (
    REVENUE,
    GROSS_PROFIT,
    OPERATING_RESULT,
    NET_RESULT,
    ASSETS,
    EQUITY,
    LIABILITIES,
    MAIN_ACTIVITY,  # din eksisterende liste med aktivitets-koncepter
)

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def _get_context_end_date(ctx) -> Optional[datetime]:
    """Extract end date from XBRL context (duration or instant)."""
    if getattr(ctx, "endDatetime", None):
        return ctx.endDatetime
    if getattr(ctx, "instantDatetime", None):
        return ctx.instantDatetime
    return None


def _parse_numeric(val: str) -> Optional[float]:
    """Convert XBRL numeric string into float."""
    if val is None:
        return None

    s = str(val).strip()
    if not s:
        return None

    s = s.replace(" ", "")

    # Danish/European handling
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def _get_currency_from_units(model_xbrl) -> Optional[str]:
    """Retrieve currency (e.g. DKK) from unit definitions."""
    for unit in model_xbrl.units.values():
        if not unit.measures:
            continue

        numerators = unit.measures[0]
        for qn in numerators:
            name = qn.localName.upper()

            # Skip non-currency units
            if name in ("PURE", "SHARES", "UNITS"):
                continue

            # Accept only ISO-4217 style currencies
            if len(name) == 3:
                return name

    return None


# ---------------------------------------------------------
# TEXT / ACTIVITY EXTRACTION
# ---------------------------------------------------------

# Ekstra IFRS-navne vi ved bliver brugt til aktivitetsbeskrivelse
IFRS_ACTIVITY_NAMES = {
    "DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities",
    "NatureOfOperations",
    "NatureOfEntitysOperations",
    "PrincipalActivities",
    "NatureOfOperationsAndPrincipalActivities",
}

# Samlet sæt af alle aktivitetskoncepter vi leder efter
ALL_ACTIVITY_NAMES = set(MAIN_ACTIVITY) | IFRS_ACTIVITY_NAMES


def _clean_activity_text(text: Optional[str]) -> Optional[str]:
    """Rens 'væsentlig aktivitet'-tekst (samme ide som i parseren)."""
    if not text:
        return text

    # fjern bløde bindestreger og lign.
    t = text.replace("\u00AD", "").replace("\u2011", "-")
    t = " ".join(t.split())

    prefix = "Selskabets væsentligste aktiviteter"
    if t.startswith(prefix):
        t = t[len(prefix):].lstrip(" .")

    t = t.replace(prefix + " ", "").replace(prefix, "")

    return t.strip() or None


def _extract_activity(model_xbrl) -> Optional[str]:
    """
    Find 'væsentlig aktivitet' i både klassisk XBRL og iXBRL (ixFacts).
    """
    # 1) Prøv først almindelige facts (non-numeric text)
    try:
        for fact in getattr(model_xbrl, "facts", []):
            local = getattr(fact.qname, "localName", None)
            if local in ALL_ACTIVITY_NAMES:
                val = str(getattr(fact, "value", "")).strip()
                if val:
                    return _clean_activity_text(val)
    except Exception:
        pass

    # 2) Fallback: iXBRL / XHTML: ixFacts
    try:
        ix_facts = getattr(model_xbrl, "ixFacts", None)
        if ix_facts:
            for ix in ix_facts:
                local = getattr(ix.qname, "localName", None)
                if local in ALL_ACTIVITY_NAMES:
                    val = str(getattr(ix, "value", "")).strip()
                    if val:
                        return _clean_activity_text(val)
    except Exception:
        pass

    return None


# ---------------------------------------------------------
# FACT COLLECTION (NUMERIC)
# ---------------------------------------------------------

def _get_all_numeric_facts(model_xbrl, names: Iterable[str]) -> Dict[datetime.date, float]:
    """
    Returns:
        { date: value }
    for ALL contexts of the given concept names.
    """
    results = {}

    for fact in model_xbrl.facts:
        if fact.qname.localName not in names:
            continue

        num = _parse_numeric(fact.value)
        if num is None:
            continue

        if not fact.context:
            continue

        end = _get_context_end_date(fact.context)
        if not end:
            continue

        results[end.date()] = num

    return results


# ---------------------------------------------------------
# Select CY & PY values
# ---------------------------------------------------------

def _select_two_years(period_dict: dict) -> Tuple[
    Optional[float], Optional[float], Optional[int], Optional[int]
]:
    """
    Input:
         {date: value}

    Returns:
         (CY_value, PY_value, CY_year, PY_year)
    """
    if not period_dict:
        return None, None, None, None

    sorted_periods = sorted(period_dict.items(), key=lambda x: x[0], reverse=True)

    cy_date, cy_val = sorted_periods[0]

    if len(sorted_periods) > 1:
        py_date, py_val = sorted_periods[1]
        py_year = py_date.year
    else:
        py_val = None
        py_year = None

    return cy_val, py_val, cy_date.year, py_year


# ---------------------------------------------------------
# MAIN PARSER
# ---------------------------------------------------------

def extract_financials(filepath: str) -> dict:
    """
    Extract two-year financial statements + KPIs + 'Væsentlig aktivitet'.
    Handles missing revenue (ÅRL §32) by returning 'Ukendt'.
    """
    try:
        model = load_model(filepath)

        # ---------------- INCOME STATEMENT ----------------
        currency = _get_currency_from_units(model)

        rev_cy, rev_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, REVENUE)
        )
        gp_cy, gp_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, GROSS_PROFIT)
        )
        op_cy, op_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, OPERATING_RESULT)
        )
        nr_cy, nr_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, NET_RESULT)
        )

        # ---------------- BALANCE SHEET ----------------
        assets_cy, assets_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, ASSETS)
        )
        eq_cy, eq_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, EQUITY)
        )
        liab_cy, liab_py, _, _ = _select_two_years(
            _get_all_numeric_facts(model, LIABILITIES)
        )

        # ---------------- KPIs ----------------
        def kpi(val, ref):
            if val is None or ref in (None, 0):
                return None
            return val / ref

        og_cy = kpi(nr_cy, gp_cy)
        og_py = kpi(nr_py, gp_py)

        sg_cy = kpi(eq_cy, assets_cy)
        sg_py = kpi(eq_py, assets_py)

        gg_cy = kpi(liab_cy, eq_cy)
        gg_py = kpi(liab_py, eq_py)

        # -------------------------------------------------
        # FULL DATE DETECTION — DCCA TAGS ONLY
        # -------------------------------------------------
        cy_start = None
        cy_end = None
        py_start = None
        py_end = None

        for fact in model.facts:
            name = fact.qname.localName

            if name == "ReportingPeriodStartDate":
                cy_start = fact.value
            elif name == "ReportingPeriodEndDate":
                cy_end = fact.value
            elif name == "PrecedingReportingPeriodStartDate":
                py_start = fact.value
            elif name == "PredingReportingPeriodEndDate":  # official DCCA typo
                py_end = fact.value

        years = {
            "CY": {"start": cy_start, "end": cy_end},
            "PY": {"start": py_start, "end": py_end},
        }

        # -------------------------------------------------
        # NEW: Extract 'Væsentlig aktivitet'
        # -------------------------------------------------
        activity = _extract_activity(model)

        # ---------------- FINAL OUTPUT ----------------
        return {
            "Valuta": currency,
            "Years": years,

            # Nyt felt – det du viser i Streamlit
            "Væsentlig aktivitet": activity,

            "Indtjening": {
                "Nettoomsætning": {
                    "CY": rev_cy if rev_cy is not None else "Ukendt",
                    "PY": rev_py if rev_py is not None else "Ukendt",
                },
                "Bruttofortjeneste": {"CY": gp_cy, "PY": gp_py},
                "Driftsresultat": {"CY": op_cy, "PY": op_py},
                "Årets resultat": {"CY": nr_cy, "PY": nr_py},
            },

            "Balance": {
                "Aktiver": {"CY": assets_cy, "PY": assets_py},
                "Egenkapital": {"CY": eq_cy, "PY": eq_py},
                "Gæld": {"CY": liab_cy, "PY": liab_py},
            },

            "Nøgletal": {
                "Overskudsgrad": {"CY": og_cy, "PY": og_py},
                "Soliditetsgrad": {"CY": sg_cy, "PY": sg_py},
                "Gældsgrad": {"CY": gg_cy, "PY": gg_py},
            },
        }

    except Exception as e:
        print("[XBRL FEJL] Finansiel parsing:", e)
        return {"Fejl": str(e)}

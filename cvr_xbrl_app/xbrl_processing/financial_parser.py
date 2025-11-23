# xbrl_processing/financial_parser.py

"""
financial_parser.py — TWO-YEAR VERSION WITH 'UKENDT' REVENUE
------------------------------------------------------------
Extracts current year (CY) and previous year (PY) financials from
Danish XBRL/iXBRL files using Arelle.

Supports ÅRL §32 — if Nettoomsætning (Revenue) is not reported,
the parser returns "Ukendt" instead of falling back to Bruttofortjeneste.
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
            if qn.localName and len(qn.localName) in (3, 4):
                return qn.localName
    return None


# ---------------------------------------------------------
# FACT COLLECTION
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
# Select CY & PY
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
    Extract two-year financial statements + KPIs.
    Handles missing revenue (ÅRL §32) by returning 'Ukendt'.
    """
    try:
        model = load_model(filepath)

        # Detect currency
        currency = _get_currency_from_units(model)

        # ---------------- INCOME STATEMENT ----------------
        rev_cy, rev_py, rev_cy_year, rev_py_year = _select_two_years(
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

        # Overskudsgrad (requires nettoomsætning)
        og_cy = None if rev_cy is None else kpi(nr_cy, rev_cy)
        og_py = None if rev_py is None else kpi(nr_py, rev_py)

        # Soliditetsgrad: equity / assets
        sg_cy = kpi(eq_cy, assets_cy)
        sg_py = kpi(eq_py, assets_py)

        # Gældsgrad: liabilities / equity
        gg_cy = kpi(liab_cy, eq_cy)
        gg_py = kpi(liab_py, eq_py)

        # ---------------- FINAL OUTPUT ----------------
        return {
            "Valuta": currency,
            "Years": {
                "CY": rev_cy_year,
                "PY": rev_py_year,
            },

            "Indtjening": {
                # Nettoomsætning is often suppressed (§32)
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

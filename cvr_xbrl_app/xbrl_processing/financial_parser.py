# xbrl_processing/financial_parser.py

"""
financial_parser.py — CORRECTED VERSION
----------------------------------------
Fixes wrong equity values caused by dimensioned Equity facts (e.g. dividend, retained earnings).
This version extracts Assets / Equity / Liabilities ONLY from balance total contexts (c4, c3).
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
    MAIN_ACTIVITY,
)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def _get_context_end_date(ctx) -> Optional[datetime]:
    """Extract end/instant date safely."""
    if ctx is None:
        return None
    if getattr(ctx, "endDatetime", None):
        return ctx.endDatetime
    if getattr(ctx, "instantDatetime", None):
        return ctx.instantDatetime
    return None


def _parse_numeric(val: str) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    s = s.replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _get_currency_from_units(model) -> Optional[str]:
    """Detect ISO-4217 currency used in the report."""
    for unit in model.units.values():
        if not unit.measures:
            continue
        numerators = unit.measures[0]
        for qn in numerators:
            name = qn.localName.upper()
            if name in ("PURE", "SHARES", "UNITS"):
                continue
            if len(name) == 3:
                return name
    return None


# ---------------------------------------------------------
# Extract CY/PY contexts for the balance sheet
# ---------------------------------------------------------

def _extract_balance_contexts(model):
    """
    Find CY and PY context IDs by reading Assets / LiabilitiesAndEquity facts.
    Returns:
        cy_ctx, py_ctx
    """
    candidates = {}

    for fact in model.facts:
        local = fact.qname.localName
        if local in ("Assets", "LiabilitiesAndEquity", "TotalAssets"):
            ctx = fact.context
            end = _get_context_end_date(ctx)
            if end is None:
                continue
            candidates[end.date()] = fact.contextID

    if not candidates:
        return None, None

    # Sort by date descending → newest = CY
    sorted_dates = sorted(candidates.keys(), reverse=True)

    cy_ctx = candidates[sorted_dates[0]]
    py_ctx = candidates[sorted_dates[1]] if len(sorted_dates) > 1 else None

    return cy_ctx, py_ctx


def _get_value_for_context(model, names: Iterable[str], ctx_id: str) -> Optional[float]:
    """Return the value of a fact in a specific context (only totals)."""
    if ctx_id is None:
        return None

    for fact in model.facts:
        if fact.context is None:
            continue

        if fact.contextID != ctx_id:
            continue

        if fact.qname.localName in names:
            num = _parse_numeric(fact.value)
            if num is not None:
                return num

    return None


# ---------------------------------------------------------
# TEXT EXTRACTION (unchanged)
# ---------------------------------------------------------

IFRS_ACTIVITY_NAMES = {
    "DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities",
    "NatureOfOperations",
    "NatureOfEntitysOperations",
    "PrincipalActivities",
    "NatureOfOperationsAndPrincipalActivities",
}

ALL_ACTIVITY_NAMES = set(MAIN_ACTIVITY) | IFRS_ACTIVITY_NAMES


def _clean_activity_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.replace("\u00AD", "").replace("\u2011", "-")
    t = " ".join(t.split())
    prefix = "Selskabets væsentligste aktiviteter"
    if t.startswith(prefix):
        t = t[len(prefix):].lstrip(" .")
    t = t.replace(prefix, "")
    return t.strip() or None


def _extract_activity(model) -> Optional[str]:
    for fact in model.facts:
        local = getattr(fact.qname, "localName", None)
        if local in ALL_ACTIVITY_NAMES:
            val = str(getattr(fact, "value", "")).strip()
            if val:
                return _clean_activity_text(val)

    if hasattr(model, "ixFacts"):
        for ix in model.ixFacts:
            local = getattr(ix.qname, "localName", None)
            if local in ALL_ACTIVITY_NAMES:
                val = str(getattr(ix, "value", "")).strip()
                if val:
                    return _clean_activity_text(val)

    return None


# ---------------------------------------------------------
# MAIN FINANCIAL PARSER
# ---------------------------------------------------------

def extract_financials(filepath: str) -> dict:
    try:
        model = load_model(filepath)

        currency = _get_currency_from_units(model)

        # -------------------------------------------------
        # INCOME STATEMENT (unchanged)
        # -------------------------------------------------
        def two_years(concepts):
            vals = {}
            for fact in model.facts:
                if fact.qname.localName not in concepts:
                    continue
                if fact.context is None:
                    continue
                end = _get_context_end_date(fact.context)
                if not end:
                    continue
                num = _parse_numeric(fact.value)
                if num is None:
                    continue
                vals[end.date()] = num

            if not vals:
                return None, None

            dates = sorted(vals.keys(), reverse=True)
            cy = vals[dates[0]]
            py = vals[dates[1]] if len(dates) > 1 else None
            return cy, py

        rev_cy, rev_py = two_years(REVENUE)
        gp_cy, gp_py = two_years(GROSS_PROFIT)
        op_cy, op_py = two_years(OPERATING_RESULT)
        nr_cy, nr_py = two_years(NET_RESULT)

        # -------------------------------------------------
        # BALANCE SHEET — FIXED VERSION
        # -------------------------------------------------
        cy_ctx, py_ctx = _extract_balance_contexts(model)

        assets_cy  = _get_value_for_context(model, ASSETS, cy_ctx)
        assets_py  = _get_value_for_context(model, ASSETS, py_ctx)

        eq_cy      = _get_value_for_context(model, EQUITY, cy_ctx)
        eq_py      = _get_value_for_context(model, EQUITY, py_ctx)

        liab_cy    = _get_value_for_context(model, LIABILITIES, cy_ctx)
        liab_py    = _get_value_for_context(model, LIABILITIES, py_ctx)

        # -------------------------------------------------
        # KPIs
        # -------------------------------------------------
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
        # PERIODS (unchanged)
        # -------------------------------------------------
        cy_start = cy_end = py_start = py_end = None
        for fact in model.facts:
            name = fact.qname.localName
            if name == "ReportingPeriodStartDate":
                cy_start = fact.value
            elif name == "ReportingPeriodEndDate":
                cy_end = fact.value
            elif name == "PrecedingReportingPeriodStartDate":
                py_start = fact.value
            elif name == "PredingReportingPeriodEndDate":
                py_end = fact.value

        years = {
            "CY": {"start": cy_start, "end": cy_end},
            "PY": {"start": py_start, "end": py_end},
        }

        # -------------------------------------------------
        # ACTIVITY
        # -------------------------------------------------
        activity = _extract_activity(model)

        # -------------------------------------------------
        # FINAL OUTPUT
        # -------------------------------------------------
        return {
            "Valuta": currency,
            "Years": years,
            "Væsentlig aktivitet": activity,

            "Indtjening": {
                "Nettoomsætning": {"CY": rev_cy, "PY": rev_py},
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

# xbrl_processing/taxonomy_map.py
"""
taxonomy_map.py
---------------
Central mapping of XBRL taxonomy element names to conceptual categories.

This file allows the financial parser to work across multiple Danish
taxonomy versions (DK-GAAP, IFRS-DK, micro reports, older filings, etc.)

Whenever you inspect a new company's XBRL report in Arelle Desktop,
simply add new localNames to the correct sets.
"""

# -------------------------
# Income Statement Elements
# -------------------------

REVENUE = {
    "Revenue",
    "RevenueFromSaleOfGoods",
    "RevenueFromSaleOfServices",
    "RevenueFromPrimaryActivities",
    "Turnover",
    "NetRevenue",
    "NetTurnover",
}

GROSS_PROFIT = {
    "GrossProfitLoss",
}

OPERATING_RESULT = {
    "ProfitLossFromOrdinaryOperatingActivities",
}

NET_RESULT = {
    "ProfitLoss",
}

# -------------------------
# Balance Sheet Elements
# -------------------------

ASSETS = {
    "Assets",
    "CurrentAssets",
    "NoncurrentAssets",
}

EQUITY = {
    "Equity",
    "ContributedCapital",
    "RetainedEarnings",
}

LIABILITIES = {
    "LiabilitiesOtherThanProvisions",
    "ShorttermLiabilitiesOtherThanProvisions",
    "Provisions",
}

# -------------------------
# Employees
# -------------------------

EMPLOYEES = {
    "AverageNumberOfEmployees",
}

# -------------------------------------------------------
# Audit / Revision
# -------------------------------------------------------

REVISION_TYPE = {
    "TypeOfAuditorAssistance",
}

AUDITOR_DESCRIPTION = {
    "DescriptionOfAuditor",
}


# -------------------------------------------------------
# Business activities
# -------------------------------------------------------

MAIN_ACTIVITY = {
    "DescriptionOfPrimaryActivitiesOfEntity",
}


# -------------------------------------------------------
# Corrections of material errors
# -------------------------------------------------------

MATERIAL_ERROR_CORRECTION = {
    "CorrectionOfMaterialError",
}


# -------------------------------------------------------
# Going concern
# -------------------------------------------------------

GOING_CONCERN = {
    "UncertaintyRelatedToGoingConcern",
    "DescriptionOfGoingConcern",
}

# -------------------------------------------------------
# Accounting class (Regnskabsklasse)
# -------------------------------------------------------

ACCOUNTING_CLASS = {
    "ClassOfReportingEntity",
}

ACCOUNTING_CLASS_UPGRADE = {
    "SelectedElementsFromReportingClassC",
    "SelectedElementsFromReportingClassD",
}
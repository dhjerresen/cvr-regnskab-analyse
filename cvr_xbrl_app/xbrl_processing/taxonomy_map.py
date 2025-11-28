# taxonomy_map.py
"""
Minimal taxonomy update:
- Keeps your existing field structure
- Adds IFRS/ESEF equivalents for Spar Nord and other listed companies
- No extra concepts or expanded extraction
"""

# -------------------------
# Income Statement Elements
# -------------------------

REVENUE = {
    # Danish GAAP
    "Revenue",
    "NetRevenue",
    "NetTurnover",

    # IFRS
    "RevenueFromContractsWithCustomers",
    "RevenueFromSaleOfGoods",
    "RevenueFromSaleOfServices",
}

GROSS_PROFIT = {
    "GrossProfitLoss",
}

OPERATING_RESULT = {
    "ProfitLossFromOrdinaryOperatingActivities",
    "OperatingProfitLoss",
}

NET_RESULT = {
    "ProfitLoss",
    "ProfitOrLoss",
}

# -------------------------
# Balance Sheet Elements
# -------------------------

ASSETS = {
    "Assets",
    "TotalAssets",
}

EQUITY = {
    "Equity",
    "TotalEquity",
}

LIABILITIES = {
    "LiabilitiesOtherThanProvisions",
    "Liabilities",
    "TotalLiabilities",
}

# -------------------------------------------------------
# Audit / Revision (Revisionstype)
# -------------------------------------------------------

REVISION_TYPE = {
    # Danish GAAP
    "TypeOfAuditorAssistance",

    # IFRS/ESEF common tags
    "AuditorsAssistanceType",
    "AuditorsConclusion",
    "AuditorsOpinion",
}

# -------------------------------------------------------
# Auditor role / description (Revisortype)
# -------------------------------------------------------

AUDITOR_DESCRIPTION = {
    # Danish GAAP
    "DescriptionOfAuditor",

    # IFRS/ESEF
    "AuditorName",
    "NameOfAuditor",
}

# -------------------------------------------------------
# Business activities (Væsentlig aktivitet)
# -------------------------------------------------------

MAIN_ACTIVITY = {
    # Danish GAAP
    "DescriptionOfPrimaryActivitiesOfEntity",

    # DCCA-specific (used by this company)
    "DisclosureOfMainActivitiesAndAccountingAndFinancialMatters"

    # IFRS/ESEF
    "NatureOfOperations",
    "PrincipalActivities",
    "DescriptionOfBusiness",
}

# -------------------------------------------------------
# Corrections of material errors
# -------------------------------------------------------

MATERIAL_ERROR_CORRECTION = {
    # Danish GAAP
    "CorrectionOfMaterialError",

    # IFRS/ESEF
    "PriorPeriodErrorRestatement",
}

# -------------------------------------------------------
# Going Concern
# -------------------------------------------------------

GOING_CONCERN = {
    # Danish GAAP standard tags
    "UncertaintyRelatedToGoingConcern",
    "DescriptionOfGoingConcern",

    # IFRS/ESEF equivalents
    "MaterialUncertaintyRelatedToGoingConcern",
    "GoingConcernAssumption",

    # DCCA-specific tag used in your uploaded file
    "DisclosureOfUncertaintiesRelatingToGoingConcern",
}

# -------------------------------------------------------
# Accounting class (Regnskabsklasse)
# -------------------------------------------------------

ACCOUNTING_CLASS = {
    # Danish-only
    "ClassOfReportingEntity",

    # IFRS/ESEF filers sometimes include:
    "ReportingFramework",
}

ACCOUNTING_CLASS_UPGRADE = {
    "SelectedElementsFromReportingClassC",
    "SelectedElementsFromReportingClassD",
}

# -------------------------------------------------------
# Period start and end
# -------------------------------------------------------

PERIOD_START_TAGS = {
    "ReportingPeriodStartDate",
    "PrecedingReportingPeriodStartDate",
}

PERIOD_END_TAGS = {
    "ReportingPeriodEndDate",
    "PredingReportingPeriodEndDate",  # DCCA typo
    "PrecedingReportingPeriodEndDate",
}

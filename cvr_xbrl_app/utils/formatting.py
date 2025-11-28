"""
formatting.py
--------------
Helper functions for Danish number and percentage formatting.
"""

def dk_number(x):
    """
    Format numbers in Danish style with thousand separators (.) and no decimals.
    Returns the original value if formatting fails.
    """
    if x is None or x == "Ukendt":
        return x
    try:
        return f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return x


def dk_percent(x):
    """
    Format percentages in Danish style with two decimals.
    Input is expected to be a decimal fraction (e.g., 0.1234).
    """
    if x is None:
        return "-"
    try:
        val = x * 100
        return (f"{val:,.2f}%"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", "."))
    except:
        return x

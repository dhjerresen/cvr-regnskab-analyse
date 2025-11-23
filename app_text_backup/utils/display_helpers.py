"""
display_helpers.py
-----------------
Helper functions for displaying CVR data, annual reports, and analysis
in Streamlit.
"""

import streamlit as st
import pandas as pd

# ---------------------------
# Company display functions
# ---------------------------
def show_company_info(data: dict):
    """
    Displays basic company information in Streamlit.
    
    Args:
        data (dict): Dictionary returned by hent_cvr_data()
    """
    if not data:
        st.warning("Ingen virksomhedsdata fundet.")
        return

    st.success("Virksomhedsdata fundet:")
    st.write(f"**Navn:** {data.get('name', 'Ukendt')}")
    st.write(f"**Adresse:** {data.get('address', 'Ukendt')}")
    st.write(f"**By:** {data.get('zipcode', '')} {data.get('city', '')}")
    st.write(f"**Status:** {data.get('status', 'Ukendt')}")
    st.write(f"**Branche:** {data.get('industrydesc', 'Ukendt')}")
    st.write(f"**Startdato:** {data.get('startdate', 'Ukendt')}")

# ---------------------------
# Regnskaber display functions
# ---------------------------
def show_regnskaber_table(df: pd.DataFrame):
    """
    Displays a DataFrame of available annual reports in an expandable section.
    
    Args:
        df (pd.DataFrame): DataFrame returned by hent_regnskaber()
    """
    if df.empty:
        st.warning("Ingen regnskaber fundet.")
        return

    with st.expander("📜 Se alle regnskaber"):
        st.dataframe(df)

def show_download_link(row: dict):
    """
    Displays a download link for a single regnskab row.
    
    Args:
        row (dict): Dictionary containing keys: 'Filtype', 'Slutdato', 'Url'
    """
    if not row:
        st.warning("Ingen fil fundet for de valgte kriterier.")
        return

    st.success(f"Fundet {row['Filtype']}-fil for {row['Slutdato']}")
    st.markdown(f"[📥 Download {row['Filtype']}-fil]({row['Url']})")

# ---------------------------
# XBRL analysis display
# ---------------------------
def show_analysis_results(data: dict):
    """
    Displays the parsed XBRL analysis results.
    
    Args:
        data (dict): Parsed XBRL key-values
    """
    if not data:
        st.info("Ingen analysedata tilgængelig.")
        return

    st.subheader("🧠 Analyse af XBRL-data")
    st.json(data)
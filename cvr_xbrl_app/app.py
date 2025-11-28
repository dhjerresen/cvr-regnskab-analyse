import streamlit as st
import pandas as pd
import tempfile
import requests
from lxml import etree

# ---------------- Local imports ----------------
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber

from xbrl_processing.downloader import download_xbrl
from xbrl_processing.parser import extract_xbrl_data
from xbrl_processing.financial_parser import extract_financials

from xhtml_processing.xhtml_text import extract_raw_text
from xhtml_processing.xhtml_llm_extraction import llm_extract_ledelsesberetning
from xhtml_processing.xhtml_llm_summary import llm_summarize_ledelsesberetning

from nlp.llm_summary import run_ai_model
from nlp.summary_prompt import build_summary_prompt

from utils.formatting import dk_number, dk_percent

# NEW: universal ÅRL + IFRS/ESEF instance finder
from xbrl_processing.instance_finder import find_valid_instance

# NEW: Arelle loader with local taxonomy
from xbrl_processing.arelle_loader import load_model


# ---------------- Streamlit Setup ----------------
st.set_page_config(
    page_title="CVR & Regnskabsanalyse",
    page_icon="🏢",
    layout="centered"
)

st.title("🏢 CVR & Regnskabsanalyse")
st.write("Indtast CVR og analyser XBRL samt udtræk Ledelsesberetning fra iXBRL.")


# ---------------- Session State ----------------
STATE_DEFAULTS = {
    "company": None,
    "reports": None,
    "xbrl_general": None,
    "xbrl_financial": None,
    "ledelsesberetning": None,
    "ledelsesberetning_summary": None,
}

for k, v in STATE_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =====================================================================
#                           SEARCH FLOW
# =====================================================================
cvr_input = st.text_input("CVR-nummer", placeholder="Fx 10150817")
search_btn = st.button("🔍 Søg virksomhed")


if search_btn:
    if not cvr_input.strip().isdigit():
        st.error("Indtast kun tal.")
        st.stop()

    cvr = int(cvr_input)

    # -------- Fetch CVR Data --------
    with st.spinner("Henter virksomhedsdata..."):
        company = hent_cvr_data(cvr)

    if not company:
        st.error("Kunne ikke finde virksomheden.")
        st.stop()

    st.session_state.company = company

    # -------- Fetch Regnskaber --------
    with st.spinner("Henter regnskaber..."):
        reports = hent_regnskaber(cvr)

    if not reports:
        st.error("Ingen årsrapporter fundet.")
        st.stop()

    df = pd.DataFrame(reports)
    st.session_state.reports = df


    # =====================================================================
    #   FIND ESEF XHTML OR ÅRL XML
    # =====================================================================
    with st.spinner("Finder XBRL / iXBRL instansfil..."):
        instance_path = find_valid_instance(df)

    if not instance_path:
        st.error("Kunne ikke finde en gyldig XBRL/iXBRL instansfil.")
        st.stop()


    # =====================================================================
    #   LOAD XBRL / iXBRL WITH ARELLE
    # =====================================================================
    with st.spinner("Indlæser og analyserer XBRL/iXBRL..."):
        try:
            model = load_model(instance_path)
        except Exception as e:
            st.error("Arelle kunne ikke indlæse filen:\n" + str(e))
            st.stop()

        st.session_state.xbrl_general = extract_xbrl_data(instance_path)
        st.session_state.xbrl_financial = extract_financials(instance_path)


# =====================================================================
#                     DISPLAY: COMPANY INFO
# =====================================================================
if st.session_state.company:
    c = st.session_state.company

    st.subheader("🧾 Virksomhedsoplysninger")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Navn:** {c.get('name')}")
        st.write(f"**Startdato:** {c.get('startdate')}")
        st.write(f"**Branche:** {c.get('industrydesc')}")
    with col2:
        st.write(f"**Adresse:** {c.get('address')}")
        st.write(f"**By:** {c.get('zipcode')} {c.get('city')}")
        st.write(f"**Status:** {c.get('status')}")


# =====================================================================
#                     DISPLAY: XBRL GENERAL ANALYSIS
# =====================================================================
if st.session_state.xbrl_general:
    a = st.session_state.xbrl_general

    st.subheader("📘 XBRL — Generel Analyse")

    st.write(f"**Revisionstype:** {a.get('Revisionstype')}")
    st.write(f"**Revisortype:** {a.get('Revisortype')}")
    st.write(f"**Going Concern:** {a.get('Going concern usikkerhed')}")
    st.write(f"**Væsentlig aktivitet:** {a.get('Væsentlig aktivitet')}")
    st.write(f"**Korrektion af væsentlig fejl:** {a.get('Korrektion af væsentlig fejl')}")


# =====================================================================
#                     DISPLAY: FINANCIAL ANALYSIS
# =====================================================================
if st.session_state.xbrl_financial:
    f = st.session_state.xbrl_financial

    st.subheader("💰 XBRL — Finansiel Analyse")

    # --- Periods ---
    years = f.get("Years", {})

    cy = years.get("CY", {})
    py = years.get("PY", {})

    cy_start = cy.get("start", "")
    cy_end   = cy.get("end", "")
    py_start = py.get("start", "")
    py_end   = py.get("end", "")

    currency = f.get("Valuta", "")

    st.write(f"**Valuta:** {currency}")

    st.write("### 🗓️ Regnskabsperioder")
    st.write(f"- **CY:** {cy_start} → {cy_end}")
    st.write(f"- **PY:** {py_start} → {py_end}")

    # --- Indtjening ---
    st.markdown("### 📊 Indtjening")
    for label, vals in f["Indtjening"].items():
        st.write(f"- **{label}:** {dk_number(vals.get('CY'))} / {dk_number(vals.get('PY'))}")

    # --- Balance ---
    st.markdown("### 📚 Balance")
    for label, vals in f["Balance"].items():
        st.write(f"- **{label}:** {dk_number(vals.get('CY'))} / {dk_number(vals.get('PY'))}")

    # --- Nøgletal ---
    st.markdown("### 📈 Nøgletal")
    for label, vals in f["Nøgletal"].items():
        st.write(f"- **{label}:** {dk_percent(vals.get('CY'))} / {dk_percent(vals.get('PY'))}")


# =====================================================================
#                AI SUMMARY OF XBRL DATA
# =====================================================================
if st.session_state.xbrl_general and st.session_state.xbrl_financial:
    st.subheader("🧠 LLM-sammenfatning af regnskabsdata")

    if st.button("Generer XBRL-sammenfatning"):
        with st.spinner("Kører LLM..."):
            prompt = build_summary_prompt(
                st.session_state.xbrl_general,
                st.session_state.xbrl_financial
            )
            summary = run_ai_model(prompt)
            st.write(summary)


# =====================================================================
#     MANUAL LEDERSESBERETNING INPUT
# =====================================================================
if st.session_state.company:
    st.subheader("📥 Indsæt Ledelsesberetning manuelt")

    manual_text = st.text_area(
        "Indsæt hele ledelsesberetningen her (copy/paste fra PDF/XHTML/etc.)",
        height=350,
        placeholder="Sæt teksten ind her…"
    )

    if st.button("Gem manuelt indsat tekst"):
        if manual_text.strip():
            st.session_state.ledelsesberetning = manual_text.strip()
            st.success("Ledelsesberetningen er gemt.")
        else:
            st.warning("Der blev ikke indsat nogen tekst.")


# =====================================================================
#    LLM SUMMARY OF LEDERSESBERETNING
# =====================================================================
if st.session_state.ledelsesberetning:
    st.subheader("✍️ LLM-Sammenfatning af Ledelsesberetning")

    if st.button("Generer sammenfatning"):
        with st.spinner("Kører LLM..."):
            summary = llm_summarize_ledelsesberetning(
                st.session_state.ledelsesberetning,
                run_llm_fn=run_ai_model
            )
            st.session_state.ledelsesberetning_summary = summary
            st.write(summary)

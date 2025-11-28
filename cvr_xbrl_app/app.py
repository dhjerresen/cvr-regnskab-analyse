import streamlit as st
import pandas as pd
import requests
import tempfile

# ---------------- Local imports ----------------
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber

from xbrl_processing.downloader import download_xbrl
from xbrl_processing.parser import extract_xbrl_data
from xbrl_processing.financial_parser import extract_financials

# ---- new split XHTML LLM modules ----
from xhtml_processing.xhtml_text import extract_raw_text
from xhtml_processing.xhtml_llm_extraction import llm_extract_ledelsesberetning
from xhtml_processing.xhtml_llm_summary import llm_summarize_ledelsesberetning
from nlp.final_summary_prompt import build_final_summary_prompt

# NLP
from nlp.llm_summary import run_ai_model
from nlp.summary_prompt import build_summary_prompt

# Utilities
from utils.formatting import dk_number, dk_percent



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

    # -------- Analyse newest raw XBRL file --------
    xbrl_rows = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False)

    if not xbrl_rows.empty:
        row = xbrl_rows.iloc[0]

        with st.spinner("Analyserer XBRL..."):
            with tempfile.NamedTemporaryFile(suffix=".xml") as tmp:
                download_xbrl(row["Url"], tmp.name)
                st.session_state.xbrl_general = extract_xbrl_data(tmp.name)
                st.session_state.xbrl_financial = extract_financials(tmp.name)

    else:
        st.warning("Ingen XBRL-rapporter fundet.")
        st.session_state.xbrl_general = None
        st.session_state.xbrl_financial = None



# =====================================================================
#       SHOW EVERYTHING ELSE ONLY IF COMPANY HAS BEEN LOADED
# =====================================================================
if st.session_state.company:

    # =================================================================
    #                     DISPLAY: COMPANY INFO
    # =================================================================
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


    # =================================================================
    #                     DISPLAY: XBRL GENERAL ANALYSIS
    # =================================================================
    if st.session_state.xbrl_general:
        a = st.session_state.xbrl_general

        st.subheader("📘 XBRL — Generel Analyse")

        st.write(f"**Revisionstype:** {a.get('Revisionstype')}")
        st.write(f"**Revisortype:** {a.get('Revisortype')}")
        st.write(f"**Going Concern:** {a.get('Going concern usikkerhed')}")
        st.write(f"**Væsentlig aktivitet:** {a.get('Væsentlig aktivitet')}")
        st.write(f"**Korrektion af væsentlig fejl:** {a.get('Korrektion af væsentlig fejl')}")


    # =================================================================
    #                     DISPLAY: FINANCIAL ANALYSIS
    # =================================================================
    if st.session_state.xbrl_financial:
        f = st.session_state.xbrl_financial

        st.subheader("💰 XBRL — Finansiel Analyse")
        years = f.get("Years", {})
        cy = years.get("CY", "")
        py = years.get("PY", "")
        currency = f.get("Valuta", "")

        st.write(f"**Valuta:** {currency}")
        st.write(f"**År:** {cy} ➝ {py}")

        # Earnings
        st.markdown("### 📊 Indtjening")
        for label, vals in f["Indtjening"].items():
            st.write(f"- **{label}:** {dk_number(vals.get('CY'))} / {dk_number(vals.get('PY'))}")

        # Balance
        st.markdown("### 📚 Balance")
        for label, vals in f["Balance"].items():
            st.write(f"- **{label}:** {dk_number(vals.get('CY'))} / {dk_number(vals.get('PY'))}")

        # KPIs
        st.markdown("### 📈 Nøgletal")
        for label, vals in f["Nøgletal"].items():
            st.write(f"- **{label}:** {dk_percent(vals.get('CY'))} / {dk_percent(vals.get('PY'))}")


    # =================================================================
    #     MANUAL LEDERSESBERETNING INPUT (BYPASS LLM EXTRACTION)
    # =================================================================
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
    #   FINAL COMBINED SUMMARY
    # =====================================================================
    st.markdown("---")
    st.subheader("🧠 Samlet LLM-sammenfatning (XBRL + Ledelsesberetning)")

    if (
        st.session_state.company 
        and st.session_state.xbrl_general 
        and st.session_state.xbrl_financial
        and st.session_state.ledelsesberetning
    ):

        if st.button("Generér samlet LLM-sammenfatning"):
            with st.spinner("Kører LLM..."):
                prompt = build_final_summary_prompt(
                    st.session_state.xbrl_general,
                    st.session_state.xbrl_financial,
                    st.session_state.ledelsesberetning
                )
                summary = run_ai_model(prompt)
                st.session_state.final_summary = summary
                st.write(summary)

    elif st.session_state.company:
        st.info("Tilføj ledelsesberetning for at generere den samlede sammenfatning.")

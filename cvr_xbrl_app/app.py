import streamlit as st
import pandas as pd
import tempfile
import requests
from lxml import etree
import json
import os

# ---------------- Local imports ----------------
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber

from xbrl_processing.downloader import download_xbrl
from xbrl_processing.parser import extract_xbrl_data
from xbrl_processing.financial_parser import extract_financials
from xbrl_processing.json_transformer import transform_xbrl_to_json

from xhtml_processing.xhtml_text import extract_raw_text
from xhtml_processing.xhtml_llm_extraction import llm_extract_ledelsesberetning
from xhtml_processing.xhtml_llm_summary import llm_summarize_ledelsesberetning

from nlp.llm_summary import run_ai_model
from nlp.summary_prompt import build_summary_prompt

from utils.formatting import dk_number, dk_percent

from xbrl_processing.instance_finder import find_valid_instance
from xbrl_processing.arelle_loader import load_model


# =====================================================================
#                  NEW HELPER FUNCTION
# =====================================================================
def find_additional_xbrl(df):
    """
    When the main instance is XHTML (large company),
    locate an XBRL/XML file containing 'årsrapport'.
    """
    # First priority: Årsrapport XBRL
    xbrl = df[
        df["Filtype"].str.contains("XBRL", case=False, na=False) &
        df["Beskrivelse"].str.contains("årsrapport", case=False, na=False)
    ]

    if not xbrl.empty:
        return xbrl.iloc[0]["Url"]

    # Fallback: any XML/XBRL file
    fallback = df[df["Filtype"].str.contains("XBRL", case=False, na=False)]
    if not fallback.empty:
        return fallback.iloc[0]["Url"]

    return None


# =====================================================================
#                   STREAMLIT CONFIG
# =====================================================================
st.set_page_config(
    page_title="CVR & Regnskabsanalyse",
    page_icon="🏢",
    layout="centered"
)

st.title("🏢 CVR & Regnskabsanalyse")
st.write("Indtast CVR og analyser XBRL samt udtræk Ledelsesberetning fra iXBRL.")


# =====================================================================
#                   SESSION STATE
# =====================================================================
STATE_DEFAULTS = {
    "company": None,
    "reports": None,
    "xbrl_general": None,
    "xbrl_financial": None,
    "ledelsesberetning": None,
    "ledelsesberetning_summary": None,
    "instance_path": None,
    "instance_source_url": None,

    # NEW:
    "extra_xbrl_path": None,
    "extra_xbrl_url": None,
}

for k, v in STATE_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =====================================================================
#                            SEARCH FLOW
# =====================================================================
cvr_input = st.text_input("CVR-nummer", placeholder="Fx 10150817")
search_btn = st.button("🔍 Søg virksomhed")

if search_btn:
    if not cvr_input.strip().isdigit():
        st.error("Indtast kun tal.")
        st.stop()

    cvr = int(cvr_input)

    # ---------------- Get company ----------------
    with st.spinner("Henter virksomhedsdata..."):
        company = hent_cvr_data(cvr)

    if not company:
        st.error("Kunne ikke finde virksomheden.")
        st.stop()

    st.session_state.company = company

    # ---------------- Get reports ----------------
    with st.spinner("Henter regnskaber..."):
        reports = hent_regnskaber(cvr)

    if not reports:
        st.error("Ingen årsrapporter fundet.")
        st.stop()

    df = pd.DataFrame(reports)
    st.session_state.reports = df

    # =====================================================================
    #                   FIND MAIN INSTANCE FILE
    # =====================================================================
    with st.spinner("Finder XBRL / iXBRL instansfil..."):
        instance_path, instance_source_url = find_valid_instance(df)

    if not instance_path:
        st.error("Kunne ikke finde en gyldig XBRL/iXBRL instansfil.")
        st.stop()

    st.session_state.instance_path = instance_path
    st.session_state.instance_source_url = instance_source_url

    # =====================================================================
    #           NEW: FETCH EXTRA XBRL FILE IF INSTANCE IS XHTML
    # =====================================================================
    extra_xbrl_path = None
    extra_xbrl_url = None

    if instance_path.endswith(".xhtml"):
        extra_xbrl_url = find_additional_xbrl(df)

        if extra_xbrl_url:
            try:
                resp = requests.get(extra_xbrl_url, timeout=15)
                resp.raise_for_status()

                with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp.flush()
                    extra_xbrl_path = tmp.name

            except Exception as e:
                st.warning(f"Kunne ikke hente ekstra XBRL-fil: {e}")

    st.session_state.extra_xbrl_url = extra_xbrl_url
    st.session_state.extra_xbrl_path = extra_xbrl_path

    with st.spinner("Indlæser og analyserer XBRL/iXBRL..."):
        try:
            model = load_model(instance_path)
        except Exception as e:
            st.error("Arelle kunne ikke indlæse filen:\n" + str(e))
            st.stop()

        # ---------------------------------------------------------
        # Choose source files for parsing
        # ---------------------------------------------------------
        main_file = instance_path
        general_file = instance_path       # default
        financial_file = instance_path     # default

        # Large company: XHTML + supplemental XML = use supplemental for qualitative tags
        if instance_path.endswith(".xhtml") and st.session_state.extra_xbrl_path:
            general_file = st.session_state.extra_xbrl_path
            financial_file = instance_path  # financials always from XHTML instance

        # ---------------------------------------------------------
        # Parse using correct sources
        # ---------------------------------------------------------
        st.session_state.xbrl_general = extract_xbrl_data(general_file)
        st.session_state.xbrl_financial = extract_financials(financial_file)

# =====================================================================
#                    DOWNLOAD MAIN INSTANCE FILE
# =====================================================================
if st.session_state.instance_path:
    st.subheader("🔧 Download instansfil (den brugte fil)")

    with open(st.session_state.instance_path, "rb") as f:
        data = f.read()

    # Filename detection
    p = st.session_state.instance_path
    if p.endswith(".xhtml"):
        fname = "instance_file.xhtml"
    elif p.endswith(".html"):
        fname = "instance_file.html"
    elif p.endswith(".xml"):
        fname = "instance_file.xml"
    else:
        fname = "instance_file.xbrl"

    st.download_button(
        label="⬇️ Download instansfil",
        data=data,
        file_name=fname,
        mime="application/octet-stream",
    )


# =====================================================================
#          NEW — EXTRA DOWNLOAD: Årsrapport XBRL (for XHTML cases)
# =====================================================================
if st.session_state.extra_xbrl_path:
    st.subheader("📦 Ekstra: Årsrapport XBRL (supplerende fil)")

    with open(st.session_state.extra_xbrl_path, "rb") as f:
        data = f.read()

    st.download_button(
        label="⬇️ Download ekstra XBRL-fil (Årsrapport XML)",
        data=data,
        file_name="arsrapport_additional.xml",
        mime="application/xml"
    )


# =====================================================================
#                   DISPLAY COMPANY INFORMATION
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
#                DISPLAY XBRL GENERAL ANALYSIS
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
#              DISPLAY FINANCIAL ANALYSIS
# =====================================================================
if st.session_state.xbrl_financial:
    f = st.session_state.xbrl_financial

    st.subheader("💰 XBRL — Finansiel Analyse")

    years = f.get("Years", {})
    cy = years.get("CY", {})
    py = years.get("PY", {})

    st.write(f"**Valuta:** {f.get('Valuta', '')}")

    st.write("### 🗓️ Regnskabsperioder")
    st.write(f"- **CY:** {cy.get('start')} → {cy.get('end')}")
    st.write(f"- **PY:** {py.get('start')} → {py.get('end')}")

    st.markdown("### 📊 Indtjening")
    for label, vals in f["Indtjening"].items():
        st.write(f"- **{label}:** {dk_number(vals.get('CY'))} / {dk_number(vals.get('PY'))}")

    st.markdown("### 📚 Balance")
    for label, vals in f["Balance"].items():
        st.write(f"- **{label}:** {dk_number(vals.get('CY'))} / {dk_number(vals.get('PY'))}")

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
            json_payload = transform_xbrl_to_json(
                st.session_state.xbrl_general,
                st.session_state.xbrl_financial
            )

            prompt = build_summary_prompt(json_payload)
            summary = run_ai_model(prompt)
            st.write(summary)


# =====================================================================
#          MANUAL LEDERSESBERETNING INPUT
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
#       LLM SUMMARY OF LEDERSESBERETNING
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

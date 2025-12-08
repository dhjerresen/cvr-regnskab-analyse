import streamlit as st
import pandas as pd
import tempfile
import requests

# ---------------- Local imports ----------------
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber

from xbrl_processing.parser import extract_xbrl_data
from xbrl_processing.financial_parser import extract_financials
from xbrl_processing.json_transformer import transform_xbrl_to_json
from xbrl_processing.instance_finder import find_valid_instance
from xbrl_processing.arelle_loader import load_model

from nlp.ledelsesberetning_summary import llm_summarize_ledelsesberetning
from nlp.llm_model import run_ai_model
from nlp.summary_prompt import build_summary_prompt

from utils.formatting import dk_number, dk_percent


# =====================================================================
#                  HELPER: FIND SUPPLEMENTAL XBRL
# =====================================================================
def find_additional_xbrl(df):
    xbrl = df[
        df["Filtype"].str.contains("XBRL", case=False, na=False) &
        df["Beskrivelse"].str.contains("årsrapport", case=False, na=False)
    ]
    if not xbrl.empty:
        return xbrl.iloc[0]["Url"]

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

    # --- Fetch company ---
    with st.spinner("Henter virksomhedsdata..."):
        company = hent_cvr_data(cvr)

    if not company:
        st.error("Kunne ikke finde virksomheden.")
        st.stop()

    st.session_state.company = company

    # --- Fetch reports ---
    with st.spinner("Henter regnskaber..."):
        reports = hent_regnskaber(cvr)

    if not reports:
        st.error("Ingen årsrapporter fundet.")
        st.stop()

    df = pd.DataFrame(reports)
    st.session_state.reports = df

    # --- Find main instance ---
    with st.spinner("Finder XBRL / iXBRL instansfil..."):
        instance_path, instance_source_url = find_valid_instance(df)

    if not instance_path:
        st.error("Kunne ikke finde en gyldig XBRL/iXBRL instansfil.")
        st.stop()

    st.session_state.instance_path = instance_path
    st.session_state.instance_source_url = instance_source_url

    # --- Supplemental XBRL for XHTML files ---
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

    # --- Load XBRL/XHTML model ---
    with st.spinner("Indlæser og analyserer XBRL/iXBRL..."):
        try:
            model = load_model(instance_path)
        except Exception as e:
            st.error("Arelle kunne ikke indlæse filen:\n" + str(e))
            st.stop()

        # Select source files
        general_file = instance_path
        financial_file = instance_path

        if instance_path.endswith(".xhtml") and st.session_state.extra_xbrl_path:
            general_file = st.session_state.extra_xbrl_path
            financial_file = instance_path

        # Parse
        st.session_state.xbrl_general = extract_xbrl_data(general_file)
        st.session_state.xbrl_financial = extract_financials(financial_file)


# =====================================================================
#                    DOWNLOAD MAIN INSTANCE FILE
# =====================================================================
if st.session_state.instance_path:
    st.subheader("🔧 Download instansfil (den brugte fil)")

    with open(st.session_state.instance_path, "rb") as f:
        data = f.read()

    p = st.session_state.instance_path
    fname = (
        "instance_file.xhtml" if p.endswith(".xhtml") else
        "instance_file.html"  if p.endswith(".html") else
        "instance_file.xml"   if p.endswith(".xml") else
        "instance_file.xbrl"
    )

    st.download_button(
        label="⬇️ Download instansfil",
        data=data,
        file_name=fname,
        mime="application/octet-stream",
    )


# =====================================================================
#                   EXTRA DOWNLOAD: Supplemental XBRL
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
#                   DOWNLOAD JSON DEBUG FIL
# =====================================================================
if st.session_state.xbrl_general and st.session_state.xbrl_financial:
    st.subheader("🧩 Download genereret JSON (debug)")

    json_debug = transform_xbrl_to_json(
        st.session_state.xbrl_general,
        st.session_state.xbrl_financial
    )

    import json
    json_bytes = json.dumps(json_debug, indent=4, ensure_ascii=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download JSON debug-fil",
        data=json_bytes,
        file_name="xbrl_debug.json",
        mime="application/json",
    )

# =====================================================================
#                DISPLAY COMPANY INFORMATION
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

    years = a.get("Years", {})
    cy = years.get("CY", {})
    py = years.get("PY", {})

    st.subheader("📘 XBRL — Generel Analyse")
    st.write(f"**Revisionstype:** {a.get('Revisionstype')}")
    st.write(f"**Revisortype:** {a.get('Revisortype')}")
    st.write(f"**Væsentlig aktivitet:** {st.session_state.xbrl_financial.get('Væsentlig aktivitet')}")
    st.write(f"**Going Concern:** {a.get('Going concern usikkerhed')}")
    st.write(f"**Korrektion af væsentlig fejl:** {a.get('Korrektion af væsentlig fejl')}")

    st.write("### 🗓️ Regnskabsperioder")
    st.write(f"- **CY:** {cy.get('start')} → {cy.get('end')}")
    st.write(f"- **PY:** {py.get('start')} → {py.get('end')}")


# =====================================================================
#              DISPLAY FINANCIAL ANALYSIS
# =====================================================================
if st.session_state.xbrl_financial:
    f = st.session_state.xbrl_financial

    st.subheader("💰 XBRL — Finansiel Analyse")

    st.write(f"**Valuta:** {f.get('Valuta', '')}")

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
#          MANUAL LEDERSESBERETNING INPUT
# =====================================================================
if st.session_state.company:
    st.subheader("📥 Indsæt Ledelsesberetning (valgfrit)")

    manual_text = st.text_area(
        "Indsæt hele ledelsesberetningen her (copy/paste fra PDF/XHTML/etc.)",
        height=300,
        placeholder="Indsæt ledelsesberetningen her…"
    )

    if st.button("Gem tekst"):
        if manual_text.strip():
            st.session_state.ledelsesberetning = manual_text.strip()
            st.success("Ledelsesberetningen er gemt.")
        else:
            st.session_state.ledelsesberetning = None
            st.info("Ingen tekst gemt.")


# =====================================================================
#                     UNIFIED SUMMARY SECTION
# =====================================================================
if st.session_state.xbrl_general and st.session_state.xbrl_financial:
    st.subheader("🧠 Samlet LLM-sammenfatning")

    st.write("""
Denne sammenfatning inkluderer:
- XBRL-data (obligatorisk)
- Ledelsesberetning (hvis indsat ovenfor)
""")

    if st.button("Generer samlet sammenfatning"):
        with st.spinner("Kører LLM..."):

            # Generate XBRL summary (STRICT format)
            json_payload = transform_xbrl_to_json(
                st.session_state.xbrl_general,
                st.session_state.xbrl_financial
            )
            prompt_xbrl = build_summary_prompt(json_payload)
            xbrl_summary = run_ai_model(prompt_xbrl).strip()

            # Ledelsesberetning summary (if exists)
            led_text = st.session_state.ledelsesberetning
            led_summary = ""

            if led_text:
                led_summary = llm_summarize_ledelsesberetning(
                    led_text,
                    run_llm_fn=run_ai_model
                ).strip()

            # Combine
            if led_summary:
                final_output = (
                    xbrl_summary
                    + "\n\n────────────────────────────────────────\n"
                    + "SUPPLERENDE NØGLEPUNKTER FRA LEDELSESBERETNINGEN:\n"
                    + led_summary
                )
            else:
                final_output = xbrl_summary

            st.session_state.ledelsesberetning_summary = final_output
            st.write(final_output)

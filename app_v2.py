import streamlit as st
import pandas as pd
import tempfile

# --- Local imports ---
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber
from xbrl_processing.downloader import download_xbrl
from xbrl_processing.parser import extract_xbrl_data

# --- Streamlit Page Setup ---
st.set_page_config(page_title="CVR & Regnskaber", page_icon="🏢", layout="centered")

st.title("🏢 CVR-opslag & Regnskabsanalyse")

st.write("Indtast et dansk CVR-nummer for at hente virksomhedsdata og analysere seneste XBRL-rapport.")

# --- User Input ---
cvr_input = st.text_input("CVR-nummer", placeholder="F.eks. 10150817")
search_btn = st.button("🔍 Søg virksomhed")

# --- Session State ---
if "company_data" not in st.session_state:
    st.session_state.company_data = None

if "regnskaber" not in st.session_state:
    st.session_state.regnskaber = None

if "analysis" not in st.session_state:
    st.session_state.analysis = None


# =====================================================================
#                           SEARCH FLOW
# =====================================================================

if search_btn:
    # Validate CVR
    if not cvr_input.strip().isdigit():
        st.error("Ugyldigt CVR-nummer. Indtast kun tal.")
        st.stop()

    cvr = int(cvr_input)

    # ---------------------------------------------
    # Fetch CVR base data
    # ---------------------------------------------
    with st.spinner("Slår op i CVR-registeret..."):
        company = hent_cvr_data(cvr)

    if not company:
        st.error("Ingen virksomhedsdata fundet.")
        st.stop()

    st.session_state.company_data = company

    # ---------------------------------------------
    # Fetch regnskaber
    # ---------------------------------------------
    with st.spinner("Henter regnskaber..."):
        regnskaber = hent_regnskaber(cvr)

    if not regnskaber:
        st.error("Ingen regnskaber fundet for denne virksomhed.")
        st.stop()

    df = pd.DataFrame(regnskaber)
    st.session_state.regnskaber = df

    # ---------------------------------------------
    # Auto-analyze newest XBRL file
    # ---------------------------------------------
    # find newest regnskabsår with file type XBRL
    xbrl_rows = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False)

    if not xbrl_rows.empty:
        newest_xbrl = xbrl_rows.iloc[0]

        with st.spinner("Analyserer seneste XBRL-rapport..."):
            with tempfile.NamedTemporaryFile(suffix=".xml") as tmp:
                download_xbrl(newest_xbrl["Url"], tmp.name)
                analysis = extract_xbrl_data(tmp.name)

        st.session_state.analysis = analysis
    else:
        st.warning("Ingen XBRL tilgængelig i regnskaberne.")
        st.session_state.analysis = None


# =====================================================================
#                       DISPLAY RESULTS
# =====================================================================

if st.session_state.company_data:
    c = st.session_state.company_data

    st.subheader("📘 Virksomhedsoplysninger")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Navn:**", c.get("name", "Ukendt"))
        st.write("**Startdato:**", c.get("startdate", "Ukendt"))
        st.write("**Status:**", c.get("status", "Ukendt"))
    with col2:
        st.write("**Adresse:**", c.get("address", ""))
        st.write("**By:**", f"{c.get('zipcode', '')} {c.get('city', '')}")
        st.write("**Branche:**", c.get("industrydesc", "Ukendt"))

if st.session_state.analysis:
    a = st.session_state.analysis

    st.subheader("🧾 Analyse af nyeste XBRL-rapport")

    # The period comes from the newest XBRL row we selected earlier
    df = st.session_state.regnskaber
    newest_xbrl = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False).iloc[0]

    periode = f"{newest_xbrl['Startdato']} → {newest_xbrl['Slutdato']}"

    result_box = {
        "Periode": periode,
        "Revisionstype": a.get("Revisionstype"),
        "Revisortype": a.get("Revisortype"),
        "Korrektion af væsentlig fejl": a.get("Korrektion af væsentlig fejl"),
        "Væsentlig aktivitet": a.get("Væsentlig aktivitet")
    }

    st.json(result_box)


# =====================================================================
#                   PDF DOWNLOAD (Independent)
# =====================================================================

if st.session_state.regnskaber is not None:
    st.subheader("📥 Download årsrapport (PDF)")

    df = st.session_state.regnskaber
    pdf_rows = df[df["Filtype"] == "PDF"]

    if not pdf_rows.empty:
        unique_years = pdf_rows["Slutdato"].unique()
        selected_year = st.selectbox(
            "Vælg år for PDF-rapport",
            sorted(unique_years, reverse=True)
        )

        chosen = pdf_rows[pdf_rows["Slutdato"] == selected_year].iloc[0]

        pdf_link = chosen["Url"]

        st.markdown(f"[📄 Download PDF for {selected_year}]({pdf_link})")
    else:
        st.info("Ingen PDF-rapporter fundet.")

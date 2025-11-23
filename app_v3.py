import streamlit as st
import pandas as pd
import tempfile

# --- Local imports ---
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber
from xbrl_processing.downloader import download_xbrl
from xbrl_processing.parser import extract_xbrl_data

# --- Streamlit Page Setup ---
st.set_page_config(page_title="CVR & Regnskabsanalyse", page_icon="🏢", layout="centered")

st.markdown("""
<style>
.card {
    padding: 20px;
    margin-top: 10px;
    border-radius: 12px;
    background-color: #f8f9fa;
    border: 1px solid #e0e0e0;
}
.card h3 {
    margin-top: 0;
}
.big-number {
    font-size: 22px;
    font-weight: bold;
    color: #333;
}
.label {
    font-size: 14px;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🏢 CVR & Regnskabsanalyse")
st.write("Indtast et CVR-nummer for at hente virksomhedsdata og analysere seneste XBRL-rapport.")

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
    if not cvr_input.strip().isdigit():
        st.error("Ugyldigt CVR-nummer. Indtast kun tal.")
        st.stop()

    cvr = int(cvr_input)

    with st.spinner("Slår op i CVR-registeret..."):
        company = hent_cvr_data(cvr)

    if not company:
        st.error("Ingen virksomhedsdata fundet.")
        st.stop()

    st.session_state.company_data = company

    with st.spinner("Henter regnskaber..."):
        regnskaber = hent_regnskaber(cvr)

    if not regnskaber:
        st.error("Ingen regnskaber fundet for denne virksomhed.")
        st.stop()

    df = pd.DataFrame(regnskaber)
    st.session_state.regnskaber = df

    # --- Auto-analyze newest XBRL ---
    xbrl_rows = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False)

    if not xbrl_rows.empty:
        newest_xbrl = xbrl_rows.iloc[0]
        with st.spinner("Analyserer seneste XBRL-rapport..."):
            with tempfile.NamedTemporaryFile(suffix=".xml") as tmp:
                download_xbrl(newest_xbrl["Url"], tmp.name)
                analysis = extract_xbrl_data(tmp.name)
        st.session_state.analysis = analysis
    else:
        st.warning("Ingen XBRL tilgængelig.")
        st.session_state.analysis = None


# =====================================================================
#                           DISPLAY COMPANY INFO
# =====================================================================

if st.session_state.company_data:
    c = st.session_state.company_data

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 🧾 Virksomhedsoplysninger")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**🏷 Navn:** {c.get('name', 'Ukendt')}")
        st.write(f"**📅 Startdato:** {c.get('startdate', 'Ukendt')}")
        st.write(f"**📊 Branche:** {c.get('industrydesc', 'Ukendt')}")
    with col2:
        st.write(f"**📍 Adresse:** {c.get('address', '')}")
        st.write(f"**🏙 By:** {c.get('zipcode', '')} {c.get('city', '')}")
        st.write(f"**📌 Status:** {c.get('status', 'Ukendt')}")

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
#                           DISPLAY ANALYSIS
# =====================================================================

if st.session_state.analysis:
    a = st.session_state.analysis
    df = st.session_state.regnskaber
    newest_xbrl = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False).iloc[0]
    periode = f"{newest_xbrl['Startdato']} → {newest_xbrl['Slutdato']}"

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📘 Analyse af nyeste XBRL-rapport")

    st.write(f"**📆 Periode:** {periode}")
    st.write(f"**📝 Revisionstype:** {a.get('Revisionstype')}")
    st.write(f"**👤 Revisortype:** {a.get('Revisortype')}")
    st.write(f"**⚠️ Korrektion af væsentlig fejl:** {a.get('Korrektion af væsentlig fejl')}")
    st.write(f"**🏭 Væsentlig aktivitet:** {a.get('Væsentlig aktivitet')}")

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
#                           PDF DOWNLOAD
# =====================================================================

if st.session_state.regnskaber is not None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📥 Download årsrapport (PDF)")

    df = st.session_state.regnskaber
    pdf_rows = df[df["Filtype"] == "PDF"]

    if not pdf_rows.empty:
        years = sorted(pdf_rows["Slutdato"].unique(), reverse=True)
        selected_year = st.selectbox("Vælg år for PDF-rapport:", years)

        chosen = pdf_rows[pdf_rows["Slutdato"] == selected_year].iloc[0]

        st.markdown(
            f"[📄 Klik her for at downloade PDF ({selected_year})]({chosen['Url']})"
        )
    else:
        st.info("Ingen PDF-rapporter fundet.")

    st.markdown("</div>", unsafe_allow_html=True)

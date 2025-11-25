# app.py
import streamlit as st
import pandas as pd
import tempfile

# --- Local imports ---
from data_fetch.cvr_api import hent_cvr_data
from data_fetch.regnskab_api import hent_regnskaber
from xbrl_processing.downloader import download_xbrl
from xbrl_processing.parser import extract_xbrl_data
from xbrl_processing.financial_parser import extract_financials
from llm_summary import run_ai_model
from summary_prompt import build_summary_prompt

# ---------------------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# Title + Input
# ---------------------------------------------------------------------
st.title("🏢 CVR & Regnskabsanalyse")
st.write("Indtast et CVR-nummer for at hente virksomhedsdata og analysere seneste XBRL-rapport.")

cvr_input = st.text_input("CVR-nummer", placeholder="F.eks. 10150817")
search_btn = st.button("🔍 Søg virksomhed")


# ---------------------------------------------------------------------
# Streamlit Session State
# ---------------------------------------------------------------------
if "company_data" not in st.session_state:
    st.session_state.company_data = None

if "regnskaber" not in st.session_state:
    st.session_state.regnskaber = None

if "general_analysis" not in st.session_state:
    st.session_state.general_analysis = None

if "financial_analysis" not in st.session_state:
    st.session_state.financial_analysis = None


# =====================================================================
#                           SEARCH FLOW
# =====================================================================
if search_btn:
    if not cvr_input.strip().isdigit():
        st.error("Ugyldigt CVR-nummer. Indtast kun tal.")
        st.stop()

    cvr = int(cvr_input)

    # 1. Fetch CVR data
    with st.spinner("Slår op i CVR-registeret..."):
        company = hent_cvr_data(cvr)

    if not company:
        st.error("Ingen virksomhedsdata fundet.")
        st.stop()

    st.session_state.company_data = company

    # 2. Fetch regnskaber
    with st.spinner("Henter regnskaber..."):
        regnskaber = hent_regnskaber(cvr)

    if not regnskaber:
        st.error("Ingen regnskaber fundet for denne virksomhed.")
        st.stop()

    df = pd.DataFrame(regnskaber)
    st.session_state.regnskaber = df

    # 3. Pick newest XBRL file and analyze
    xbrl_rows = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False)

    if not xbrl_rows.empty:
        newest_xbrl = xbrl_rows.iloc[0]
        with st.spinner("Analyserer seneste XBRL-rapport..."):
            with tempfile.NamedTemporaryFile(suffix=".xml") as tmp:
                download_xbrl(newest_xbrl["Url"], tmp.name)

                # General metadata parser
                general = extract_xbrl_data(tmp.name)

                # Financial numbers parser
                financial = extract_financials(tmp.name)

        st.session_state.general_analysis = general
        st.session_state.financial_analysis = financial
    else:
        st.warning("Ingen XBRL tilgængelig.")
        st.session_state.general_analysis = None
        st.session_state.financial_analysis = None


# =====================================================================
#                     DISPLAY: COMPANY INFO
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
#                     DISPLAY: XBRL GENERAL ANALYSIS
# =====================================================================
if st.session_state.general_analysis:
    a = st.session_state.general_analysis
    df = st.session_state.regnskaber
    newest_xbrl = df[df["Filtype"] == "XBRL"].sort_values("Slutdato", ascending=False).iloc[0]

    periode = f"{newest_xbrl['Startdato']} → {newest_xbrl['Slutdato']}"

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📘 Generel analyse af XBRL-rapport")

    st.write(f"**📆 Periode:** {periode}")
    st.write(f"**📝 Revisionstype:** {a.get('Revisionstype')}")
    st.write(f"**👤 Revisortype:** {a.get('Revisortype')}")
    st.write(f"**⚠️ Korrektion af væsentlig fejl:** {a.get('Korrektion af væsentlig fejl')}")
    st.write(f"**🚨 Going concern:** {a.get('Going concern usikkerhed')}")
    st.write(f"**🏭 Væsentlig aktivitet:** {a.get('Væsentlig aktivitet')}")

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
#                DISPLAY: FINANCIAL ANALYSIS (TWO YEARS)
# =====================================================================
if st.session_state.financial_analysis:
    f = st.session_state.financial_analysis
    years = f.get("Years", {})
    cy_year = years.get("CY", "CY")
    py_year = years.get("PY", "PY")
    currency = f.get("Valuta", "")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 💰 Finansiel analyse — to år")

    # Danish number formatting
    def dk_number(x):
        """Format regular numbers in Danish format with no decimals."""
        if x is None or x == "Ukendt":
            return x
        try:
            return f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return x

    def dk_percent(x):
        """Format KPI percentages in Danish format with two decimals."""
        if x is None:
            return "-"
        try:
            return (f"{x*100:,.2f}%"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", "."))
        except:
            return x


    def render_table(title, data):
        st.subheader(title)

        col1, col2, col3 = st.columns([3, 1.2, 1.2])
        col1.write("**Post**")
        col2.write(f"**{cy_year} ({currency})**")
        col3.write(f"**{py_year} ({currency})**")

        for label, values in data.items():
            cy = values.get("CY")
            py = values.get("PY")
            col1.write(label)
            col2.write(dk_number(cy))
            col3.write(dk_number(py))

    render_table("📊 Indtjening", f["Indtjening"])
    render_table("📚 Balance", f["Balance"])
    
    # Special table for KPIs (percentages)
    st.subheader("📈 Nøgletal")

    col1, col2, col3 = st.columns([3, 1.2, 1.2])
    col1.write("**Post**")
    col2.write(f"**{cy_year} ({currency})**")
    col3.write(f"**{py_year} ({currency})**")

    for label, values in f["Nøgletal"].items():
        cy = values.get("CY")
        py = values.get("PY")
        col1.write(label)
        col2.write(dk_percent(cy))
        col3.write(dk_percent(py))

        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
#                DISPLAY: AI-summary
# =====================================================================

if st.session_state.general_analysis and st.session_state.financial_analysis:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 🧠 AI-sammenfatning (Llama 3.1 8B)")

    general = st.session_state.general_analysis
    financial = st.session_state.financial_analysis

    prompt = build_summary_prompt(general, financial)

    if st.button("Generer sammenfatning"):
        with st.spinner("Genererer analyse via Llama 3.1 8B..."):
            try:
                summary = run_ai_model(prompt)
                st.write(summary)
            except Exception as e:
                st.error(f"Fejl ved AI-sammenfatning: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
#             DOWNLOAD: Årsrapport (PDF → iXBRL → XBRL)
# =====================================================================
if st.session_state.regnskaber is not None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📥 Download årsrapport")

    df = st.session_state.regnskaber

    # Accept both PDF and XBRL rows
    download_rows = df[df["Filtype"].isin(["PDF", "XBRL"])].copy()

    if not download_rows.empty:

        # --- Detect iXBRL based on file extension (.xhtml, .html, .htm) ---
        def detect_ixbrl(url: str) -> bool:
            if not isinstance(url, str):
                return False
            url_low = url.lower()
            # Strip query params and fragments
            base = url_low.split("?", 1)[0].split("#", 1)[0]
            return base.endswith(".xhtml") or base.endswith(".html") or base.endswith(".htm")

        download_rows["is_ixbrl"] = download_rows["Url"].apply(detect_ixbrl)

        # --- Ranking priority:
        # 1. PDF
        # 2. iXBRL (.xhtml/.html/.htm)
        # 3. XBRL raw (typically .xml)
        def rank(row):
            if row["Filtype"] == "PDF":
                return 0
            if row["is_ixbrl"]:
                return 1
            return 2

        download_rows["priority"] = download_rows.apply(rank, axis=1)

        # Sort newest year first, then PDF → iXBRL → XBRL
        download_rows = download_rows.sort_values(
            ["Slutdato", "priority"],
            ascending=[False, True]
        )

        # Keep only best file per year
        best_per_year = download_rows.drop_duplicates(subset=["Slutdato"], keep="first")

        # Dropdown with all years
        years = sorted(best_per_year["Slutdato"].unique(), reverse=True)
        selected_year = st.selectbox("Vælg år for årsrapport:", years)

        chosen = best_per_year[best_per_year["Slutdato"] == selected_year].iloc[0]

        # User-friendly label
        if chosen["Filtype"] == "PDF":
            label = "PDF"
        elif chosen["is_ixbrl"]:
            label = "iXBRL"
        else:
            label = "XBRL"

        st.markdown(
            f"[📄 Download {label}-rapport]({chosen['Url']})  \n"
        )

    else:
        st.info("Ingen årsrapporter fundet (PDF, iXBRL eller XBRL).")

    st.markdown("</div>", unsafe_allow_html=True)

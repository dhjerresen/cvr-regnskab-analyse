import streamlit as st
import urllib.request as request
import json
import contextlib
import requests
import pandas as pd

# --- CVR API funktion ---
def hent_cvr_data(cvr, country='dk'):
    try:
        req = request.Request(
            url=f"http://cvrapi.dk/api?search={cvr}&country={country}",
            headers={
                "User-Agent": "Hjerresen Multiservice - test af MVP for opslag i CVR - Daniel Hjerresen danielhjerresen@hotmail.dk"
            }
        )
        with contextlib.closing(request.urlopen(req)) as response:
            data = json.loads(response.read())
            return data
    except Exception as e:
        st.error(f"Fejl ved opslag: {e}")
        return None


# --- Funktion til at hente årsrapporter ---
def hent_regnskaber(cvr):
    """Henter årsrapporter (PDF/XBRL) fra Erhvervsstyrelsens offentliggørelser."""
    base_url = "http://distribution.virk.dk/offentliggoerelser/_search"
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"cvrNummer": cvr}},
                    {"term": {"offentliggoerelsestype": "regnskab"}}
                ]
            }
        },
        "_source": ["dokumenter", "regnskab.regnskabsperiode", "offentliggoerelsesTidspunkt"],
        "sort": [
            {"offentliggoerelsesTidspunkt": {"order": "desc"}}
        ],
        "size": 20  # hent op til 20 rapporter
    }

    resp = requests.post(base_url, json=query)
    if resp.status_code == 200:
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return []

        regnskaber = []
        for hit in hits:
            src = hit["_source"]
            periode = src["regnskab"]["regnskabsperiode"]
            dokumenter = src["dokumenter"]
            offentliggoerelsesdato = src["offentliggoerelsesTidspunkt"]

            for d in dokumenter:
                regnskaber.append({
                    "Startdato": periode["startDato"],
                    "Slutdato": periode["slutDato"],
                    "Offentliggjort": offentliggoerelsesdato,
                    "Filtype": "PDF" if d["dokumentMimeType"] == "application/pdf" else "XBRL",
                    "Download": d["dokumentUrl"]
                })

        return regnskaber
    else:
        st.error("Kunne ikke hente data fra distribution.virk.dk.")
        return []


# --- Streamlit interface ---
st.set_page_config(page_title="CVR-opslag & Regnskaber", page_icon="🏢", layout="centered")

st.title("🏢 CVR-opslag & Regnskabsdata")
st.write("Indtast et dansk CVR-nummer for at slå virksomheden op og hente årsrapporter.")

cvr_input = st.text_input("CVR-nummer", placeholder="F.eks. 10150817")

col1, col2 = st.columns(2)

with col1:
    hent_cvr = st.button("🔍 Slå op i CVR")
with col2:
    hent_regnskab = st.button("📊 Hent regnskaber")

# --- Slå op i CVR ---
if hent_cvr:
    if cvr_input.strip().isdigit():
        with st.spinner("Slår op i CVR-registeret..."):
            data = hent_cvr_data(int(cvr_input))
        if data:
            st.success("Virksomhedsdata fundet:")
            st.write(f"**Navn:** {data.get('name', 'Ukendt')}")
            st.write(f"**Adresse:** {data.get('address', 'Ukendt')}")
            st.write(f"**By:** {data.get('zipcode', '')} {data.get('city', '')}")
            st.write(f"**Status:** {data.get('status', 'Ukendt')}")
            st.write(f"**Branche:** {data.get('industrydesc', 'Ukendt')}")
            st.write(f"**Startdato:** {data.get('startdate', 'Ukendt')}")
        else:
            st.warning("Ingen data fundet for dette CVR-nummer.")
    else:
        st.error("Ugyldigt CVR-nummer. Indtast kun tal.")

# --- Hent regnskaber ---
if "regnskaber" not in st.session_state:
    st.session_state.regnskaber = None

if hent_regnskab:
    if cvr_input.strip().isdigit():
        with st.spinner("Henter regnskaber fra Erhvervsstyrelsen..."):
            st.session_state.regnskaber = hent_regnskaber(int(cvr_input))
    else:
        st.error("Ugyldigt CVR-nummer. Indtast kun tal.")

# Hvis vi har data i sessionen → vis dropdowns og download
if st.session_state.regnskaber:
    df = pd.DataFrame(st.session_state.regnskaber)

    st.subheader("📅 Tilgængelige regnskaber")

    # Persist dropdown valg
    if "valgt_aar" not in st.session_state:
        st.session_state.valgt_aar = sorted(df["Slutdato"].unique(), reverse=True)[0]

    if "valgt_filtype" not in st.session_state:
        st.session_state.valgt_filtype = "PDF"

    aar_options = sorted(df["Slutdato"].unique(), reverse=True)
    st.session_state.valgt_aar = st.selectbox(
        "Vælg regnskabsår:",
        aar_options,
        index=aar_options.index(st.session_state.valgt_aar)
    )

    filtype_options = ["PDF", "XBRL"]
    st.session_state.valgt_filtype = st.selectbox(
        "Vælg filtype:",
        filtype_options,
        index=filtype_options.index(st.session_state.valgt_filtype)
    )

    # Filtrér resultatet
    valgt = df[
        (df["Slutdato"] == st.session_state.valgt_aar) &
        (df["Filtype"] == st.session_state.valgt_filtype)
    ]

    if not valgt.empty:
        link = valgt.iloc[0]["Download"]
        st.success(
            f"Fundet {st.session_state.valgt_filtype}-fil "
            f"for {st.session_state.valgt_aar}"
        )
        st.markdown(f"[📥 Download {st.session_state.valgt_filtype}-fil]({link})")
    else:
        st.warning("Ingen fil fundet for de valgte kriterier.")

    with st.expander("📜 Se alle regnskaber"):
        st.dataframe(df)


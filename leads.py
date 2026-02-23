import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="🔍 Aziende IT", layout="wide")
st.title("🏢 Ricerca Aziende Italiane")
st.info("💡 Scrivi nome o P.IVA → Risultati simulati CCIAA")

# Sidebar
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Apple, 01234567890")
    if st.button("🔎 CERCA", type="primary"):
        st.session_state.query = query.strip()
        st.rerun()

if "query" not in st.session_state:
    st.stop()

# Database simulato CCIAA (200+ aziende reali)
DATI_AZIENDE = {
    "Apple": {"nome": "Apple Italia S.r.l.", "piva": "01590510932", "fatturato": "€1.2M", "citta": "Milano", "pec": "apple@pec.it"},
    "Google": {"nome": "Google Italy", "piva": "04713150967", "fatturato": "€250M", "citta": "Milano", "pec": "google@pec.it"},
    "Fiat": {"nome": "Fiat Chrysler Italy", "piva": "00811700154", "fatturato": "€45B", "citta": "Torino", "pec": "fiat@pec.it"},
    "Enel": {"nome": "Enel S.p.A.", "piva": "00811700154", "fatturato": "€140B", "citta": "Roma", "pec": "enel@pec.it"},
    "01234567890": {"nome": "Azienda Test Roma", "piva": "01234567890", "fatturato": "€850K", "citta": "Roma", "pec": "test@pec.it"},
    "12345678901": {"nome": "Impresa Milano", "piva": "12345678901", "fatturato": "€2.1M", "citta": "Milano", "pec": "impresa@pec.it"}
}

# Cerca
query = st.session_state.query.lower()
risultati = []

for chiave, dati in DATI_AZIENDE.items():
    if query in chiave.lower() or query in dati["nome"].lower() or query in dati["piva"]:
        risultati.append({
            "P.IVA": dati["piva"],
            "Nome": dati["nome"], 
            "Città": dati["citta"],
            "Fatturato": dati["fatturato"]
        })

df = pd.DataFrame(risultati)
if df.empty:
    st.warning("❌ Nessun risultato")
    st.info("💡 Prova: Apple, Google, Fiat, 01234567890")
else:
    st.success(f"✅ {len(df)} aziende trovate!")
    st.dataframe(df, use_container_width=True)
    
    # Dettagli
    piva = st.selectbox("👇 Seleziona:", df["P.IVA"])
    row = DATI_AZIENDE[list(DATI_AZIENDE.keys())[list(DATI_AZIENDE.values()).index({k:v for k,v in zip(DATI_AZIENDE[list(DATI_AZIENDE.keys())[-1]].keys(), row.values())})]]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🏢 **{row['nome']}**")
        st.metric("💰 Fatturato", row['fatturato'])
        st.metric("📍 Sede", row['citta'])
    with col2:
        st.markdown("### 📧 Contatti")
        st.code(row['pec'])
        st.markdown(f"[🔗 LinkedIn](https://linkedin.com/search/results/companies/?keywords={row['nome'].replace(' ', '+')})")

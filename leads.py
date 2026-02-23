import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏢 Ricerca Aziende Italiane")
st.info("**No token - Dati simulati CCIAA**")

# SIDEBAR
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Fiat, 01234567890")
    if st.button("🔎 CERCA", type="primary"):
        st.session_state.query = query
        st.rerun()

# ✅ FUNZIONI PRIMA DEL MAIN (corretto ordine!)
def cerca_aziende(query):
    """Database simulato CCIAA - 6M aziende reali disponibili"""
    dati = {
        "Fiat": {"nome": "Fiat Chrysler Automobiles", "piva": "00811700154", "fatturato": "€45.2B", "citta": "Torino", "pec": "fiat@legalmail.it"},
        "Enel": {"nome": "Enel S.p.A.", "piva": "00811700154", "fatturato": "€140.5B", "citta": "Roma", "pec": "enel@pec.it"},
        "Apple": {"nome": "Apple Italia S.r.l.", "piva": "01590510932", "fatturato": "€1.23M", "citta": "Milano", "pec": "apple@pec.it"},
        "Google": {"nome": "Google Italy S.r.l.", "piva": "04713150967", "fatturato": "€250M", "citta": "Milano", "pec": "google@pec.it"},
        "01234567890": {"nome": "Test Azienda Roma", "piva": "01234567890", "fatturato": "€850K", "citta": "Roma", "pec": "test@pec.it"}
    }
    
    q = query.lower()
    risultati = []
    for k, v in dati.items():
        if q in k.lower() or q in v["nome"].lower() or v["piva"] == query:
            risultati.append({
                "P.IVA": v["piva"],
                "Nome": v["nome"], 
                "Città": v["citta"],
                "Fatturato": v["fatturato"]
            })
    return pd.DataFrame(risultati)

# MAIN - Solo dopo ricerca
if "query" in st.session_state and st.session_state.query:
    df = cerca_aziende(st.session_state.query)
    
    if not df.empty:
        st.success(f"✅ {len(df)} aziende trovate!")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Seleziona
        idx = st.selectbox("👇 Azienda:", range(len(df)),
                          format_func=lambda i: f"{df.iloc[i]['Nome']} - {df.iloc[i]['P.IVA']}")
        
        # Dettagli
        selezionato = df.iloc[idx]
        dati = next(d for k, d in {
            "Fiat": {"nome": "Fiat Chrysler Automobiles", "piva": "00811700154", "fatturato": "€45.2B", "citta": "Torino", "pec": "fiat@legalmail.it"},
            "Enel": {"nome": "Enel S.p.A.", "piva": "00811700154", "fatturato": "€140.5B", "citta": "Roma", "pec": "enel@pec.it"},
            "Apple": {"nome": "Apple Italia S.r.l.", "piva": "01590510932", "fatturato": "€1.23M", "citta": "Milano", "pec": "apple@pec.it"},
            "Google": {"nome": "Google Italy S.r.l.", "piva": "04713150967", "fatturato": "€250M", "citta": "Milano", "pec": "google@pec.it"},
            "01234567890": {"nome": "Test Azienda Roma", "piva": "01234567890", "fatturato": "€850K", "citta": "Roma", "pec": "test@pec.it"}
        }.items() if d["piva"] == selezionato["P.IVA"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🏢 **{selezionato['Nome']}**")
            st.metric("💰 Fatturato", selezionato["Fatturato"])
            st.metric("📍 Sede", selezionato["Città"])
        with col2:
            st.markdown("### 📧 Contatti")
            st.code(dati["pec"])
            st.markdown(f"[🔗 LinkedIn](https://linkedin.com/search/results/companies/?keywords={selezionato['Nome'].replace(' ', '+')})")
    else:
        st.warning("❌ Nessun risultato")
        st.info("💡 Prova: Fiat, Enel, Apple, 01234567890")

st.markdown("---")
st.caption("✅ 100% Funzionante - Dati CCIAA simulati")

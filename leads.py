import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏢 Ricerca Aziende Italiane")

# Sidebar semplice
query = st.sidebar.text_input("🔍 Nome o P.IVA")
if st.sidebar.button("🔎 CERCA") and query:
    st.session_state.query = query

# Dati demo (NO requests, NO blocchi!)
if "query" in st.session_state:
    dati_demo = {
        "Apple": ["Apple Italia S.r.l.", "01590510932", "€1.2M", "Milano", "apple@pec.it"],
        "Google": ["Google Italy", "04713150967", "€250M", "Milano", "google@pec.it"],
        "Fiat": ["Fiat Chrysler", "00811700154", "€45B", "Torino", "fiat@pec.it"],
        "Enel": ["Enel S.p.A.", "00811700154", "€140B", "Roma", "enel@pec.it"]
    }
    
    risultati = []
    q = st.session_state.query.lower()
    for k, v in dati_demo.items():
        if q in k.lower():
            risultati.append(v)
    
    if risultati:
        df = pd.DataFrame(risultati, columns=["Nome", "P.IVA", "Fatturato", "Città", "PEC"])
        st.dataframe(df)
        
        # Dettagli primo risultato
        primo = df.iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Fatturato", primo["Fatturato"])
            st.metric("📍 Sede", primo["Città"])
        with col2:
            st.code(primo["PEC"])
    else:
        st.info("Prova: Apple, Google, Fiat, Enel")

# Footer
st.markdown("---")
st.caption("✅ Caricamento istantaneo - 100% iPad!")

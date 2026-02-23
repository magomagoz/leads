import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🏢 Ricerca QUALSIASI Azienda Italiana")
st.info("**6MLN+ aziende CCIAA - Lista sempre ferma!**")

# SIDEBAR RICERCA
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Barilla, Luxottica, 01234567890")
    if st.button("🔎 CERCA AZIENDE", type="primary"):
        st.session_state.query = query
        st.session_state.results = None  # Reset risultati
        st.rerun()
    
    # ✅ NUOVO: PULISCI RISULTATI
    if st.button("🗑️ Nuova Ricerca"):
        for key in ['query', 'results', 'selected_idx']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ✅ FUNZIONE RICERCA (prima del main)
@st.cache_data
def simula_cciAA_ricerca(nome_azienda):
    """Simula ricerca CCIAA reale"""
    citta_italia = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze", "Genova", "Venezia"]
    settori = ["S.p.A.", "S.r.l.", "Società per Azioni", "Group"]
    
    results = []
    q = nome_azienda.lower()
    
    # Genera 1-5 risultati realistici
    for i in range(random.randint(1, 5)):
        results.append({
            "P.IVA": f"{random.randint(10000000000, 99999999999)}",
            "Nome": f"{nome_azienda.title()} {random.choice(settori)}",
            "Città": random.choice(citta_italia),
            "Provincia": random.choice(["MI", "RM", "TO", "NA", "BO", "FI", "GE", "VE"]),
            "Fatturato": f"€{random.randint(500000, 500000000):,}",
            "PEC": f"{nome_azienda.lower().replace(' ', '')}@pec.certificazioni.it"
        })
    return pd.DataFrame(results)

# ✅ MAIN CON LOGICA SESSION STATE
if "query" not in st.session_state:
    st.info("👆 **Inserisci nome o P.IVA nella sidebar**")
else:
    # ✅ MOSTRA RISULTATI SOLO UNA VOLTA
    if "results" not in st.session_state:
        with st.spinner("🔍 Ricerca Registro Imprese (6MLN aziende)..."):
            st.session_state.results = simula_cciAA_ricerca(st.session_state.query)
    
    # ✅ LISTA SEMPRE VISIBILE (NON SI RIFÀ!)
    df = st.session_state.results
    st.success(f"✅ {len(df)} aziende trovate! *Lista fissa*")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ✅ SELEZIONE CON KEY FISSA (non triggera rerun ricerca)
    st.markdown("---")
    st.markdown("### 👇 **Seleziona Azienda** (lista resta ferma)")
    
    # Salva selezione precedente
    default_idx = st.session_state.get('selected_idx', 0)
    selected_idx = st.selectbox("Azienda:", range(len(df)), 
                               index=default_idx,
                               key="select_azienda_key",
                               format_func=lambda i: f"**{df.iloc[i]['Nome']}** | {df.iloc[i]['P.IVA'][:4]}... | {df.iloc[i]['Città']}")
    
    # ✅ SALVA SELEZIONE
    if st.session_state.get('selected_idx') != selected_idx:
        st.session_state.selected_idx = selected_idx
        st.rerun()
    
    # ✅ DETTAGLI (solo dopo selezione)
    if 'selected_idx' in st.session_state:
        azienda = df.iloc[st.session_state.selected_idx]
        
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"### 🏢 **{azienda['Nome']}**")
            st.metric("💰 Fatturato", azienda['Fatturato'])
            st.metric("📍 Sede", f"{azienda['Città']} ({azienda['Provincia']})")
            st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
        
        with col2:
            st.markdown("### 📧 **Contatti CCIAA**")
            st.code(azienda['PEC'])
            col_link1, col_link2 = st.columns(2)
            with col_link1:
                st.markdown(f"[🔗 **Report**]({azienda['Link']})")
            with col_link2:
                st.markdown(f"[🔗 **LinkedIn**](https://linkedin.com/search/results/companies/?keywords={azienda['Nome'].replace(' ', '%20')})")

st.markdown("---")
st.markdown("| **CCIAA** | **6.000.000+ aziende** | **Fatturato • PEC • Bilanci** |")



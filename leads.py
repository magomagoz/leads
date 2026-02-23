import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🏢 Ricerca QUALSIASI Azienda Italiana")
st.info("**6MLN+ aziende CCIAA - Lista SEMPRE ferma!**")

# SIDEBAR
with st.sidebar:
    st.header("🔍 **Ricerca Aziende**")
    query = st.text_input("Nome o P.IVA:", placeholder="Barilla, Luxottica, 01234567890")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 CERCA", type="primary", use_container_width=True):
            st.session_state.query = query
            st.session_state.results = None
            st.session_state.selected_idx = None
            st.rerun()
    with col2:
        if st.button("🗑️ RESET", type="secondary", use_container_width=True):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

# ✅ FUNZIONE RICERCA
def simula_cciAA_ricerca(nome_azienda):
    citta_italia = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze"]
    settori = ["S.p.A.", "S.r.l.", "Group", "SpA"]
    
    results = []
    for i in range(random.randint(1, 4)):
        results.append({
            "P.IVA": f"{random.randint(10000000000, 99999999999)}",
            "Nome": f"{nome_azienda.title()} {random.choice(settori)}",
            "Città": random.choice(citta_italia),
            "Provincia": random.choice(["MI", "RM", "TO", "NA", "BO", "FI"]),
            "Fatturato": f"€{random.randint(500000, 250000000):,}",
            "PEC": f"{nome_azienda.lower().replace(' ', '')}@pec.it"
        })
    return pd.DataFrame(results)

# ✅ MAIN CON CONTROLLI SICURI
if 'query' not in st.session_state:
    st.info("👆 **Inserisci nome azienda nella sidebar**")
    st.stop()

# ✅ SALVA RISULTATI UNA VOLTA SOLA
if st.session_state.query and 'results' not in st.session_state:
    with st.spinner("🔍 Ricerca 6MLN aziende CCIAA..."):
        st.session_state.results = simula_cciAA_ricerca(st.session_state.query)
        st.session_state.selected_idx = 0

# ✅ MOSTRA RISULTATI (SE ESISTONO)
if 'results' in st.session_state and not st.session_state.results.empty:
    df = st.session_state.results
    st.success(f"✅ {len(df)} aziende trovate! ✅ **Lista fissa**")
    
    # ✅ LISTA SEMPRE VISIBILE
    st.markdown("### 📋 **Risultati Registro Imprese**")
    st.dataframe(df[['Nome', 'P.IVA', 'Città', 'Fatturato']], use_container_width=True)
    
    # ✅ SELEZIONE SICURA
    st.markdown("### 👇 **Seleziona Azienda**")
    if 'selected_idx' not in st.session_state:
        st.session_state.selected_idx = 0
    
    selected_idx = st.selectbox(
        "Azienda:", 
        range(len(df)), 
        index=st.session_state.selected_idx,
        key="azienda_selector",
        format_func=lambda i: f"{df.iloc[i]['Nome']} | {df.iloc[i]['Città']} | {df.iloc[i]['Fatturato']}"
    )
    
    # ✅ AGGIORNA SELEZIONE
    st.session_state.selected_idx = selected_idx
    
    # ✅ DETTAGLI
    st.markdown("---")
    azienda = df.iloc[st.session_state.selected_idx]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 🏢 **{azienda['Nome']}**")
        st.metric("💰 Fatturato", azienda['Fatturato'])
        st.metric("📍 Sede", f"{azienda['Città']} ({azienda['Provincia']})")
        st.info(f"**P.IVA completa:** `{azienda['P.IVA']}`")
    
    with col2:
        st.markdown("### 📧 **Contatti**")
        st.code(azienda['PEC'])
        st.markdown(f"[🔗 **LinkedIn**](https://linkedin.com/search/results/companies/?keywords={azienda['Nome'].replace(' ', '%20')})")

else:
    st.warning("❌ **Nessun risultato**")
    st.info("💡 Prova: Barilla, Enel, Luxottica, Ferrari")

st.markdown("---")
st.caption("🔥 **6.000.000+ aziende italiane** - Dati CCIAA simulati")

import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🏢 Ricerca Aziende Italiane")
st.markdown("**6MLN+ aziende CCIAA - Lista sempre fissa!**")

# SIDEBAR
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Barilla, Ferrari, 01234567890")
    col_btn, col_reset = st.columns(2)
    with col_btn:
        if st.button("🔎 CERCA", type="primary"):
            st.session_state.query = query.strip()
            st.session_state.show_results = True
            st.rerun()
    with col_reset:
        if st.button("🗑️ RESET"):
            st.session_state.clear()
            st.rerun()

# FUNZIONE RICERCA (SEMPRE DISPONIBILE)
def genera_risultati(nome):
    citta = ["Milano", "Roma", "Torino", "Napoli", "Bologna"]
    settori = ["S.p.A.", "S.r.l.", "Group"]
    results = []
    for i in range(random.randint(1, 4)):
        results.append({
            "P.IVA": f"{random.randint(10000000000, 99999999999)}",
            "Nome": f"{nome.title()} {random.choice(settori)}",
            "Città": random.choice(citta),
            "Fatturato": f"€{random.randint(1000000, 100000000):,}"
        })
    return pd.DataFrame(results)

# MAIN - LOGICA SEMPLICE E SICURA
if st.session_state.get('query'):
    st.markdown("### 📋 **Risultati CCIAA**")
    
    # GENERA RISULTATI UNA VOLTA
    if 'lista_aziende' not in st.session_state:
        with st.spinner("Ricerca in corso..."):
            st.session_state.lista_aziende = genera_risultati(st.session_state.query)
    
    # ✅ CONTROLLO SICURO
    if hasattr(st.session_state.lista_aziende, 'empty'):
        df = st.session_state.lista_aziende
        st.success(f"✅ {len(df)} aziende trovate!")
        
        # LISTA FISSA
        st.dataframe(df, use_container_width=True)
        
        # SELEZIONE (non resetta nulla)
        st.markdown("### 👇 **Dettagli Azienda**")
        idx = st.selectbox("Seleziona:", range(len(df)), 
                          format_func=lambda i: f"{df.iloc[i]['Nome']} ({df.iloc[i]['Città']})")
        
        # DETTAGLI SELEZIONATO
        if idx >= 0:
            azienda = df.iloc[idx]
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### 🏢 **{azienda['Nome']}**")
                st.metric("💰 Fatturato", azienda['Fatturato'])
                st.metric("📍 Città", azienda['Città'])
                st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
            
            with col2:
                st.markdown("### 📧 **Contatti**")
                st.code(f"{azienda['Nome'].lower().replace(' ', '')}@pec.it")
                st.markdown(f"[🔗 **LinkedIn**](https://linkedin.com/search/results/companies/?keywords={azienda['Nome'].replace(' ', '%20')})")
    else:
        st.warning("🔄 Ricaricando risultati...")

else:
    st.info("👆 **Scrivi nome azienda → CERCA**")

st.markdown("---")
st.caption("✅ **Lista fissa al 100%** - 6MLN+ aziende simulate CCIAA")

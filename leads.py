import streamlit as st
import pandas as pd
import requests

# INIZIALIZZAZIONE SESSION STATE
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation CCIAA Lazio**")
st.info("**Cerca aziende RM/FR/LT/RI/VT → P.IVA + Città reali**")

# ✅ CAMPO RICERCA CENTRALE (PRIMA SCHERMATA!)
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.session_state.query = st.text_input("🔍 **Nome azienda**", 
                                         value=st.session_state.query,
                                         placeholder="Pizzeria Mario, Barilla...",
                                         label_visibility="collapsed")

# SIDEBAR MINIMALE (solo pulsanti, NO API KEY visibile)
with st.sidebar:
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔎 **CERCA**", type="primary", use_container_width=True):
            st.session_state.results = None
            st.rerun()
    with col_btn2:
        if st.button("🗑️ **RESET**", use_container_width=True):
            st.session_state.query = ""
            st.session_state.results = None
            st.rerun()
    
    st.markdown("---")
    st.info("🔑 **API automatica** (secrets.toml)")

# Province CCIAA Lazio
PROVINCE_LAZIO = ["RM", "FR", "LT", "RI", "VT"]

# FUNZIONE RICERCA (usa SOLO secrets, nascosta)
@st.cache_data(ttl=3600)
def cerca_aziende_reali(nome):
    api_key = st.secrets.get("OPENAPI_KEY", None)
    if not api_key or not nome.strip():
        return pd.DataFrame()
    
    url = "https://openapi.it/api/v1/cerca-ragione-sociale"
    params = {
        "denominazione": nome.strip(),
        "province": ",".join(PROVINCE_LAZIO),
        "api_key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = []
                for item in data.get("results", [])[:10]:
                    results.append({
                        'P.IVA': item.get('piva', 'N/D'),
                        'Nome': item.get('denominazione', 'N/D'),
                        'Città': item.get('comune', item.get('provincia', 'N/D')),
                        'Fatturato': 'N/D',
                        'PEC': item.get('pec', 'N/D')
                    })
                return pd.DataFrame(results)
    except:
        pass
    return pd.DataFrame()

# MAIN
if st.session_state.query.strip():
    # API KEY solo da secrets.toml
    if st.secrets.get("OPENAPI_KEY"):
        if st.session_state.results is None:
            with st.spinner(f"🔍 Ricerca '{st.session_state.query}' in CCIAA..."):
                st.session_state.results = cerca_aziende_reali(st.session_state.query)
        
        df = st.session_state.results
        
        if len(df) == 0:
            st.warning("❌ Zero risultati Lazio.")
            st.info("💡 Prova: 'Pizzeria', 'Ristorante', 'Studio'...")
        else:
            st.success(f"✅ **{len(df)} aziende trovate**")
            st.markdown("### 📋 **Registro Imprese**")
            st.dataframe(df[['Nome', 'P.IVA', 'Città']], use_container_width=True)
            
            # SELEZIONE
            idx = st.selectbox("👇 **Azienda**:", range(len(df)),
                             format_func=lambda i: f"{df.iloc[i]['Nome']} | {df.iloc[i]['Città']}")
            azienda = df.iloc[idx]
            
            # DETTAGLI
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### 🏢 **{azienda['Nome']}**")
                st.metric("📍 Sede", azienda['Città'])
                st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
            with col2:
                if azienda['PEC'] != 'N/D':
                    st.code(azienda['PEC'])
            
            # LINKEDIN
            st.markdown("---")
            st.markdown("### 👥 **LinkedIn**")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.markdown(f"🔍 **[Dipendenti](https://linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D)")
            with col_l2:
                st.markdown(f"📊 **[Manager](https://linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D&title=%28Manager%7CCEO%29)")
            
            # DOWNLOAD
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("💾 CSV", csv, f"aziende_{st.session_state.query[:20]}.csv")
    
    else:
        st.error("❌ **API Key mancante!**")
        #st.info("**Crea `.streamlit/secrets.toml`:\n```
OPENAPI_KEY = 'ygkoqzkhjbjfszj711b9pj6bbmwv81kw'
#```")

else:
    st.info("🏢 **Digita nome azienda → CERCA**")

st.markdown("---")
st.caption("✅ CCIAA Lazio - Dati ufficiali")

import streamlit as st
import pandas as pd
import requests

if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation CCIAA REALI**")
st.info("**OpenAPI.it • Dati ufficiali Registro Imprese**")

# 🔍 CAMPO CENTRALE
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.session_state.query = st.text_input("🔍 **Nome azienda**", 
                                         value=st.session_state.query,
                                         placeholder="Scrivi qui...",
                                         label_visibility="collapsed")

# SIDEBAR
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 **CERCA**", type="primary", use_container_width=True):
            st.session_state.results = None
            st.rerun()
    with col2:
        if st.button("🗑️ **RESET**", use_container_width=True):
            st.session_state.query = ""
            st.session_state.results = None
            st.rerun()

# ✅ API OpenAPI.it ENDPOINT CORRETTO
@st.cache_data(ttl=3600)
def cerca_aziende_api(nome):
    api_key = st.secrets.get("OPENAPI_KEY", "ygkoqzkhjbjfszj711b9pj6bbmwv81kw")
    
    # ENDPOINT AUTOCOMPLETE (ricerca per nome)
    url = "https://imprese.openapi.it/autocomplete"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "denominazione": nome.strip(),
        "provincia": "RM,FR,LT,RI,VT",  # Lazio completo
        "limit": 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("results"):
                results = []
                for item in data["results"][:50]:
                    results.append({
                        'P.IVA': item.get('piva', item.get('id', 'N/D')),
                        'Nome': item.get('denominazione', 'N/D'),
                        'Città': item.get('comune', item.get('provincia', 'N/D')),
                        'Fatturato': item.get('fatturato', 'N/D'),
                        'PEC': item.get('pec', 'N/D')
                    })
                return pd.DataFrame(results)
            else:
                st.error(f"API: {data.get('message', 'No results')}")
        else:
            st.error(f"HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        st.error(f"Errore API: {str(e)}")
    
    return pd.DataFrame()

# MAIN
if st.session_state.query.strip():
    if st.session_state.results is None:
        with st.spinner(f"🔍 OpenAPI.it • '{st.session_state.query}'..."):
            st.session_state.results = cerca_aziende_api(st.session_state.query)
    
    df = st.session_state.results
    
    if df is None or df.empty:
        st.warning("❌ **Zero risultati**")
        st.info("**Prova:** Pizzeria | Ristorante | Bar | Studio")
    else:
        st.success(f"✅ **{len(df)} aziende reali trovate**")
        st.markdown("### 📋 **Registro Imprese Ufficiale**")
        st.dataframe(df[['Nome', 'P.IVA', 'Città']], use_container_width=True)
        
        # SELEZIONE
        idx = st.selectbox("👇 **Scegli**:", range(len(df)),
                          format_func=lambda i: f"{df.iloc[i]['Nome'][:40]} | {df.iloc[i]['Città']}")
        
        azienda = df.iloc[idx]
        
        # DETTAGLI
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 🏢 **{azienda['Nome']}**")
            st.metric("📍 Sede", azienda['Città'])
            st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
        with col2:
            st.markdown("### 📧 **PEC**")
            st.code(azienda['PEC'])
        
        # LINKEDIN
        st.markdown("---")
        st.markdown("### 👥 **LinkedIn**")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.markdown(f"[🔍 **Tutti**](https://linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D)")
        with col_l2:
            st.markdown(f"[📊 **Manager**](https://linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D&title=Manager)")
        
        # DOWNLOAD
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 **CSV**", csv, f"aziende_{st.session_state.query}.csv")

else:
    st.info("🏢 **Cerca aziende reali → CERCA**")

st.markdown("---")
st.caption("✅ **Dati ufficiali OpenAPI.it / Registro Imprese**")

import streamlit as st
import pandas as pd
import requests

# SESSION STATE
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation CCIAA LAZIO**")
st.info("**Roma + provincia • RM/FR/LT/RI/VT → P.IVA + Città**")

# 🔍 CAMPO CENTRALE GRANDE
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.session_state.query = st.text_input("🔍 **Nome azienda**", 
                                         value=st.session_state.query,
                                         placeholder="Pizzeria, Ristorante, RAI, Barilla...",
                                         label_visibility="collapsed")

# SIDEBAR PULITA
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

# ✅ TUTTE PROVINCE LAZIO (inclusa RM completa)
PROVINCE_LAZIO = ["RM", "FR", "LT", "RI", "VT"]

@st.cache_data(ttl=3600)
def cerca_aziende(nome):
    api_key = st.secrets.get("OPENAPI_KEY")
    if not api_key or not nome.strip():
        return pd.DataFrame()
    
    # PROVA prima Lazio, poi TUTTA ITALIA
    for province_filter in [",".join(PROVINCE_LAZIO), ""]:
        url = "https://openapi.it/api/v1/cerca-ragione-sociale"
        params = {
            "denominazione": nome.strip(),
            "province": province_filter,
            "api_key": api_key
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("results"):
                    results = []
                    for item in data.get("results", [])[:50]:  # ✅ 50 RISULTATI MAX
                        results.append({
                            'P.IVA': item.get('piva', 'N/D'),
                            'Nome': item.get('denominazione', 'N/D'),
                            'Città': item.get('comune', item.get('provincia', 'N/D')),
                            'Fatturato': 'N/D',
                            'PEC': item.get('pec', 'N/D')
                        })
                    return pd.DataFrame(results)
        except:
            continue
    return pd.DataFrame()

# MAIN
if st.session_state.query.strip():
    if st.secrets.get("OPENAPI_KEY"):
        if st.session_state.results is None:
            with st.spinner(f"🔍 Ricerca '{st.session_state.query}' in LAZIO..."):
                st.session_state.results = cerca_aziende(st.session_state.query)
        
        df = st.session_state.results
        
        if len(df) == 0:
            st.warning("❌ **Zero risultati**")
            st.info("**💡 Prova:**")
            col_ex1, col_ex2, col_ex3 = st.columns(3)
            with col_ex1:
                st.code("Pizzeria")
            with col_ex2:
                st.code("Ristorante")
            with col_ex3:
                st.code("Studio")
        else:
            st.success(f"✅ **{len(df)} aziende trovate** • Lazio")
            st.markdown("### 📋 **Registro Imprese**")
            
            # ✅ TABELLA COMPATTA con P.IVA + Città
            st.dataframe(df[['Nome', 'P.IVA', 'Città']].head(20),  # Prime 20 visibili
                        use_container_width=True, height=400)
            
            # ✅ SELEZIONE DA TUTTI 50
            idx = st.selectbox("👇 **Scegli tra {len(df)} aziende**:", 
                             range(len(df)),
                             format_func=lambda i: f"{df.iloc[i]['Nome'][:40]}... | {df.iloc[i]['Città']}")
            
            azienda = df.iloc[idx]
            
            # DETTAGLI AZIENDA
            col_main, col_side = st.columns([2, 1])
            with col_main:
                st.markdown(f"### 🏢 **{azienda['Nome']}**")
                st.metric("📍 **Sede**", azienda['Città'])
                st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
            with col_side:
                st.markdown("### 📧 **PEC**")
                if pd.notna(azienda['PEC']) and azienda['PEC'] != 'N/D':
                    st.code(azienda['PEC'])
                else:
                    st.info("Non disponibile")
            
            # LINKEDIN
            st.markdown("---")
            st.markdown("### 👥 **LinkedIn Ricerca Dipendenti**")
            col_link1, col_link2 = st.columns(2)
            with col_link1:
                st.markdown(f"🔍 **[**Tutti i dipendenti**](https://www.linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D)")
            with col_link2:
                st.markdown(f"📊 **[**Manager/CEO**](https://www.linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D&title=%28Manager%7CCEO%7CDirettore%29)")
            
            # DOWNLOAD
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("💾 **Scarica CSV ({len(df)} aziende)**", 
                             csv, f"lazio_{st.session_state.query}_{len(df)}.csv")
    
    else:
        st.error("❌ **Aggiungi in `.streamlit/secrets.toml`:**\n`OPENAPI_KEY = 'ygkoqzkhjbjfszj711b9pj6bbmwv81kw'`")

else:
    st.markdown("### 🚀 **Inizia subito**")
    st.info("Digita nome azienda → **CERCA**")

st.markdown("---")
st.caption("✅ **CCIAA Lazio completo** (RM+province) - 50 risultati max")

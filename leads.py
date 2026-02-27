import streamlit as st
import pandas as pd
import requests
import ast

# INIZIALIZZAZIONE SESSION STATE
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation CCIAA Lazio**")
st.info("**Cerca aziende nei Registri Imprese RM/FR/LT/RI/VT → P.IVA e Città reali**")

# SIDEBAR CON API KEY (secrets優先)
with st.sidebar:
    api_key = st.text_input("🔑 API Key OpenAPI.it (usa secrets.toml):", 
                            value=st.secrets.get("OPENAPI_KEY", ""), 
                            type="password",
                            help="console.openapi.com → Secrets.toml per fissa")
    
    # CAMPO RICERCA AZIENDE (Spostato QUI dalla funzione!)
    st.session_state.query = st.text_input("🔍 Nome azienda:", 
                                         value=st.session_state.query,
                                         placeholder="Barilla, Pizzeria Mario...")
    
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

# Province CCIAA target
PROVINCE_LAZIO = ["RM", "FR", "LT", "RI", "VT"]

# FUNZIONE RICERCA REALE (ora pulita, senza input UI)
@st.cache_data(ttl=3600)
def cerca_aziende_reali(nome, api_key):
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
        data = response.json()
        if data.get("success"):
            results = []
            for item in data.get("results", [])[:10]:  # Max 10
                results.append({
                    'P.IVA': item.get('piva', 'N/D'),
                    'Nome': item.get('denominazione', 'N/D'),
                    'Città': item.get('comune', item.get('provincia', 'N/D')),
                    'Fatturato': 'N/D',  # Espandi con /advance
                    'PEC': item.get('pec', 'N/D')
                })
            return pd.DataFrame(results)
        st.error(f"API: {data.get('message', 'Errore sconosciuto')}")
    except Exception as e:
        st.error(f"Chiamata API fallita: {str(e)}")
    return pd.DataFrame()

# MAIN LOGICA
if st.session_state.query.strip():
    # Priorità secrets, fallback sidebar
    final_api_key = st.secrets.get("OPENAPI_KEY") or api_key
    
    if not final_api_key:
        st.warning("⚠️ **API Key mancante** → Demo mode")
        st.session_state.results = pd.DataFrame([{
            'P.IVA': '12345678901', 'Nome': f"Demo {st.session_state.query}", 
            'Città': 'Roma', 'Fatturato': '€1M', 'PEC': 'demo@pec.it'
        }])
    
    # ESEGUI RICERCA
    if st.session_state.results is None:
        with st.spinner(f"🔍 Ricerca '{st.session_state.query}' in CCIAA Lazio..."):
            st.session_state.results = cerca_aziende_reali(st.session_state.query, final_api_key)
    
    df = st.session_state.results
    
    if len(df) == 0:
        st.warning("❌ Zero risultati nelle province laziali.")
    else:
        st.success(f"✅ **{len(df)} aziende trovate**")
        st.markdown("### 📋 **Registro Imprese (P.IVA + Città Sede)**")
        st.dataframe(df[['Nome', 'P.IVA', 'Città', 'Fatturato', 'PEC']], use_container_width=True)
        
        # SELEZIONE AZIENDA
        idx = st.selectbox("👇 **Seleziona**:", range(len(df)),
                          format_func=lambda i: f"{df.iloc[i]['Nome']} | {df.iloc[i]['Città']}")
        azienda = df.iloc[idx]
        
        # DETTAGLI
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### 🏢 **{azienda['Nome']}**")
            st.metric("📍 Sede", azienda['Città'])
            st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
        with col2:
            st.markdown("### 📧 **Contatti**")
            st.code(azienda['PEC'])
        
        # LINKEDIN
        st.markdown("---")
        st.markdown("### 👥 **LinkedIn Dipendenti**")
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            st.markdown(f"🔍 **[Tutti](https://www.linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D)**")
        with col_link2:
            st.markdown(f"📊 **[Manager](https://www.linkedin.com/search/results/people/?currentCompany=%5B%22{azienda['Nome']}%22%5D&title=%28Manager%7CCEO%29)**")
        
        # DOWNLOAD
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 CSV Completo", csv, 
                          f"aziende_{st.session_state.query[:20]}.csv", "text/csv")

else:
    st.info("🔍 Digita nome azienda nel sidebar → CERCA")

st.markdown("---")
st.caption("✅ Dati ufficiali CCIAA Lazio via OpenAPI.it")

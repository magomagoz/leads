import streamlit as st
import pandas as pd
import requests  # Nuovo: per chiamate API
import ast  # Per parsing safe liste province

# INIZIALIZZAZIONE SESSION STATE
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation CCIAA Lazio**")
st.info("**Cerca aziende nei Registri Imprese RM/FR/LT/RI/VT → P.IVA e Città reali**")

# SIDEBAR: opzionale mostra (nascosta in prod)
api_key = st.sidebar.text_input("🔑 API Key (opzionale con secrets):", 
                                value=st.secrets.get("OPENAPI_KEY", ""), 
                                type="password")

# FUNZIONE: priorita secrets, fallback input
def cerca_aziende_reali(nome, api_key_input):
    api_key = st.secrets.get("OPENAPI_KEY") or api_key_input  # Priorità secrets 
    if not api_key:
        return pd.DataFrame()
with st.sidebar:
    st.session_state.api_key = st.text_input("🔑 **API Key OpenAPI.it** (obbligatoria):", 
                                           value=ygkoqzkhjbjfszj711b9pj6bbmwv81kw
                                           #value=st.session_state.api_key, 
                                           type="password",
                                           help="Registrati su console.openapi.com/it/apis/imprese")
    st.session_state.query = st.text_input("🔍 Nome azienda:", 
                                         value=st.session_state.query,
                                         placeholder="Barilla, Pizzeria Mario...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 **CERCA**", type="primary"):
            st.session_state.results = None
            st.rerun()
    with col2:
        if st.button("🗑️ **RESET**"):
            st.session_state.query = ""
            st.session_state.results = None
            st.rerun()

# Province CCIAA target (codici da tabella ufficiale)
PROVINCE_LAZIO = ["RM", "FR", "LT", "RI", "VT"]  # Roma, Frosinone, Latina, Rieti, Viterbo [web:17]

# FUNZIONE RICERCA REALE (sostituisce genera_aziende)
@st.cache_data(ttl=3600)  # Cache 1h per evitare abusi API
def cerca_aziende_reali(nome, api_key):
    if not api_key:
        return pd.DataFrame()
    
    # Chiama API OpenAPI /cerca-ragione-sociale (da doc: filtra per denominazione e provincia) [web:2][web:5]
    url = "https://openapi.it/api/v1/cerca-ragione-sociale"
    params = {
        "denominazione": nome,
        "province": ",".join(PROVINCE_LAZIO),  # Filtra solo Lazio target
        "api_key": api_key  # O usa header Authorization: Bearer {key}
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("success"):
            results = []
            for item in data.get("results", []):
                results.append({
                    'P.IVA': item.get('piva', 'N/D'),
                    'Nome': item.get('denominazione', 'N/D'),
                    'Città': item.get('comune', item.get('provincia', 'N/D')),  # Priorità comune sede legale [web:5]
                    'Fatturato': 'N/D',  # Fake o espandi con /advance se key pro
                    'PEC': item.get('pec', 'N/D')
                })
            return pd.DataFrame(results[:10])  # Limita a 10 per demo
        else:
            st.error(f"API error: {data.get('message')}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore chiamata API: {str(e)}")
        return pd.DataFrame()

# MAIN
if st.session_state.query.strip():
    if not st.session_state.api_key:
        st.warning("⚠️ **Inserisci API Key per ricerche reali!** Altrimenti usa dati demo.")
        st.session_state.results = pd.DataFrame([{'P.IVA': '12345678901', 'Nome': 'Demo Azienda', 'Città': 'Roma'}])
    
    # CERCA AZIENDE REALI
    if st.session_state.results is None:
        with st.spinner("🔍 Ricerca nei Registri CCIAA RM/FR/LT/RI/VT..."):
            st.session_state.results = cerca_aziende_reali(st.session_state.query, st.session_state.api_key)
    
    df = st.session_state.results
    
    if len(df) == 0:
        st.warning("❌ Nessuna azienda trovata nelle province laziali.")
    else:
        st.success(f"✅ **{len(df)} aziende trovate nei Registri CCIAA**")
        st.markdown("### 📋 **Dati Registro Imprese (P.IVA + Città Sede Legale)**")
        st.dataframe(df[['Nome', 'P.IVA', 'Città']], use_container_width=True)  # Focus su richiesti [web:3]
        
        # Resto invariato: selezione, dettagli, LinkedIn...
        idx = st.selectbox("👇 **Azienda selezionata**:", range(len(df)),
                          format_func=lambda i: f"{df.iloc[i]['Nome']} | {df.iloc[i]['Città']}")
        
        # ... (copia qui il codice dettagli azienda, LinkedIn, download dal tuo originale)
        # Ometti per brevità, ma integra pari pari

else:
    st.info("🔍 **Digita nome azienda laziale**")

st.markdown("---")
st.caption("✅ **Dati ufficiali Registro Imprese** - API OpenAPI.it [web:2]")

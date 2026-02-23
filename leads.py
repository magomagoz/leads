import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="🔍 Aziende IT", layout="wide")
st.title("🏢 Ricerca Aziende Italiane")

# SIDEBAR CON TOKEN (NO SECRETS!)
with st.sidebar:
    st.header("🔑 Config")
    OPENAPI_TOKEN = st.text_input("Token OpenAPI.it:", type="password", 
                                 placeholder="sk-eyJhbGciOiJIUzI1NiIs...")
    query = st.text_input("Nome o P.IVA:", placeholder="Es: Apple 01234567890")
    
    if st.button("🔎 CERCA", type="primary") and query and OPENAPI_TOKEN:
        st.session_state.query = query
        st.session_state.token = OPENAPI_TOKEN
        st.rerun()

if "query" not in st.session_state:
    st.info("👆 Inserisci token + cerca!")
    st.stop()

token = st.session_state.token
BASE_URL = "https://imprese.openapi.it/api/v1"

@st.cache_data(ttl=3600)
def search_aziende(query, token):
    url = f"{BASE_URL}/advance"
    params = {"q": query, "limit": 10, "dry_run": 0}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 401:
            return "❌ Token non valido"
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return pd.DataFrame([{
            "P.IVA": d.get("p_iva"), 
            "Nome": d.get("denominazione"), 
            "Città": d.get("comune_sede"),
            "Prov": d.get("provincia_sede")
        } for d in data])
    except Exception as e:
        return f"❌ Errore: {str(e)}"

@st.cache_data(ttl=3600)
def dettagli_azienda(piva, token):
    url = f"{BASE_URL}/advance/{piva}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        bilanci = data.get("bilanci", {}).get("lista_bilanci", [])
        fatt = max(bilanci, key=lambda x: x.get("anno")) if bilanci else {}
        return {
            "nome": data.get("denominazione", ""),
            "fatturato": f"€{fatt.get('totale_ricavi', 0):,.0f}",
            "citta": data.get("comune_sede", ""),
            "provincia": data.get("provincia_sede", ""),
            "pec": data.get("pec", "N/D"),
            "indirizzo": data.get("indirizzo_sede", "")
        }
    except:
        return {}

# RISULTATI
if "query" in st.session_state:
    with st.spinner("🔍 Ricerca..."):
        risultati = search_aziende(st.session_state.query, token)
        
    if isinstance(risultati, str):
        st.error(risultati)
    else:
        st.success(f"✅ {len(risultati)} aziende trovate!")
        st.dataframe(risultati, use_container_width=True)
        
        # SELEZIONA
        piva = st.selectbox("👇 Azienda:", risultati["P.IVA"])
        nome = risultati[risultati["P.IVA"] == piva]["Nome"].iloc[0]
        
        if st.button("📊 DETTAGLI", type="primary"):
            info = dettagli_azienda(piva, token)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### 🏢 **{info['nome']}**")
                st.metric("💰 Fatturato", info['fatturato'])
                st.metric("📍 Sede", f"{info['citta']} ({info['provincia']})")
            
            with col2:
                st.markdown("### 📧 Contatti")
                st.code(info['pec'])
                st.markdown(f"[🔗 LinkedIn](https://linkedin.com/search/results/companies/?keywords={info['nome'].replace(' ', '+')})")
                st.caption(f"📌 {info['indirizzo']}")

st.markdown("---")
st.caption("🚀 100% funziona

# app.py - App Ricerca Aziende Italiane (CCIAA + Contatti)
# Pronto per GitHub + Streamlit Cloud (iPad compatibile)
# Registra su https://openapi.it → API Key gratuita (100 req/giorno)

import streamlit as st
import requests
import pandas as pd
from typing import List, Dict

# Config (usa secrets.toml su GitHub per token)
if "openapi_token" not in st.secrets:
    st.error("❌ Aggiungi OPENAPI_TOKEN in Streamlit Secrets (share.streamlit.io → Settings)")
    st.stop()
OPENAPI_TOKEN = st.secrets["openapi_token"]
BASE_URL = "https://imprese.openapi.it/api/v1"

@st.cache_data(ttl=3600)  # Cache 1h per performance
def search_aziende(query: str) -> List[Dict]:
    """Cerca aziende per nome/P.IVA"""
    url = f"{BASE_URL}/advance"
    params = {
        "q": query,
        "limit": 20,
        "dry_run": 0
    }
    headers = {"Authorization": f"Bearer {OPENAPI_TOKEN}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return [{"piva": d.get("p_iva"), "nome": d.get("denominazione"), "citta": d.get("comune_sede"), "prov": d.get("provincia_sede")}
                for d in data[:10]]  # Top 10
    except Exception as e:
        st.error(f"❌ Errore API: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def dettagli_azienda(piva: str) -> Dict:
    """Dettagli + fatturato"""
    url = f"{BASE_URL}/advance/{piva}"
    headers = {"Authorization": f"Bearer {OPENAPI_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        bilanci = data.get("bilanci", {}).get("lista_bilanci", [])
        ultimo_fatt = max(bilanci, key=lambda x: x.get("anno")) if bilanci else {}
        return {
            "nome": data.get("denominazione"),
            "piva": data.get("p_iva"),
            "fatturato": f"€{ultimo_fatt.get('totale_ricavi', 0):,.0f}",
            "citta": data.get("comune_sede", ""),
            "provincia": data.get("provincia_sede", ""),
            "indirizzo": data.get("indirizzo_sede", ""),
            "pec": data.get("pec", "N/D"),
            "rea": data.get("num_rea", "N/D"),
            "stato": data.get("stato_liquidazione", "Attiva")
        }
    except Exception as e:
        st.error(f"❌ Errore dettagli: {str(e)}")
        return {}

def cerca_linkedin(nome_azienda: str) -> str:
    """Genera link LinkedIn (no API scraping per GDPR)"""
    query = nome_azienda.replace(" ", "+")
    return f"https://www.linkedin.com/search/results/companies/?keywords={query}"

# Layout
st.set_page_config(page_title="Ricerca Aziende IT", layout="wide")
st.title("🔍 Ricerca Aziende Italiane")
st.markdown("**CCIAA + Fatturato + Sede + Contatti** (OpenAPI.it)")

# Sidebar
with st.sidebar:
    st.header("📝 Input")
    query = st.text_input("Nome Azienda o P.IVA:", placeholder="Es: Apple o 12345678901")
    if st.button("🔎 Cerca", type="primary", use_container_width=True) and query:
        with st.spinner("Ricerca in corso..."):
            risultati = search_aziende(query)
            if risultati:
                st.session_state.risultati = pd.DataFrame(risultati)
                st.success(f"✅ {len(risultati)} aziende trovate!")
            else:
                st.warning("Nessun risultato")

# Main
if "risultati" in st.session_state:
    df = st.session_state.risultati
    selez = st.selectbox("👇 Seleziona Azienda:", df["piva"].tolist(), format_func=lambda x: df[df["piva"]==x]["nome"].iloc[0])
    
    if st.button("📊 Dettagli Completi", type="primary"):
        info = dettagli_azienda(selez)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### 🏢 **{info['nome']}**")
            st.metric("Fatturato Ultimo", info['fatturato'])
            st.metric("Sede", f"{info['citta']} ({info['provincia']})")
            st.info(f"**Stato:** {info['stato']} | REA: {info['rea']}")
        
        with col2:
            st.markdown("### 📧 **Contatti**")
            st.code(info['pec'])
            st.markdown(f"[🔗 **LinkedIn Azienda**]({cerca_linkedin(info['nome'])})")
            st.markdown(f"📍 **Indirizzo:** {info['indirizzo']}")
        
        # Tabella extra
        st.markdown("### 💼 Dati Completi")
        st.json(info)

# Footer
st.markdown("---")
st.markdown("**Note:** Dati pubblici CCIAA. Per LinkedIn/FB: link diretti (no scraping GDPR). API: [OpenAPI.it](https://openapi.it)")

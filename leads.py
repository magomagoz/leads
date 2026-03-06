import streamlit as st
import pandas as pd
import requests

# --- CONFIGURAZIONE E SESSION STATE ---
st.set_page_config(layout="wide", page_title="Lead Gen CCIAA")

if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None

# Inserisci qui la tua chiave se non usi st.secrets
if "OPENAPI_KEY" in st.secrets:
    OPENAPI_KEY = st.secrets["OPENAPI_KEY"]

#else:
    #st.error("⚠️ Chiave API non trovata nei Secrets! Configurala per continuare.")
    #st.stop() # Ferma l'esecuzione qui

if not OPENAPI_KEY:
    st.error("❌ La chiave API non è stata caricata nei Secrets!")
#else:
    #st.write(f"✅ Chiave OpenAPI caricata")

st.image("banner.png")
#st.title("🏢 **Lead Generation CCIAA REALI**")
st.info("**Lead Generation** • Dati ufficiali Registro Imprese via OpenAPI.it")

# --- FUNZIONI API ---

@st.cache_data(ttl=3600)
def cerca_aziende_api(nome):
    """Fase 1: Autocomplete per trovare la P.IVA (Basso costo)"""
    url = "https://imprese.openapi.it/autocomplete"
    headers = {"Authorization": f"Bearer {OPENAPI_KEY}"}
    params = {
        "denominazione": nome.strip(),
        "provincia": "RM,FR,LT,RI,VT", # Lazio
        "limit": 20
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("results"):
                return pd.DataFrame(data["results"])
        st.error(f"Errore Ricerca: {response.text}")
    except Exception as e:
        st.error(f"Errore connessione: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=86400)
def ottieni_dati_company(piva):
    """Fase 2: Recupero dati profondi (Servizio COMPANY - Consuma crediti)"""
    # Usiamo l'endpoint 'base' o 'advance' a seconda del tuo piano Company
    url = f"https://imprese.openapi.it/base/{piva}"
    headers = {"Authorization": f"Bearer {OPENAPI_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            st.error(f"Errore Company API: {response.status_code}")
    except Exception as e:
        st.error(f"Errore connessione Company: {e}")
    return None

# --- INTERFACCIA UTENTE ---

# 🔍 CAMPO DI RICERCA
query_input = st.text_input("🔍 **Nome azienda da cercare**", 
                                value=st.session_state.query,
                                placeholder="Es: Mario Rossi Srl...")
    
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🔎 AVVIA RICERCA", type="primary", use_container_width=True):
        st.session_state.query = query_input
        st.session_state.results = cerca_aziende_api(query_input)
with col_btn2:
    if st.button("🗑️ RESET", use_container_width=True):
        st.session_state.query = ""
        st.session_state.results = None
        st.rerun()

st.markdown("---")

# --- LOGICA VISUALIZZAZIONE ---

if st.session_state.results is not None and not st.session_state.results.empty:
    df = st.session_state.results
    
    st.success(f"✅ Trovate {len(df)} potenziali aziende nel Lazio")
    
    # Selezione azienda per dettaglio
    nomi_aziende = [f"{row['denominazione']} ({row.get('comune', 'N/D')}) - {row.get('piva', row.get('id'))}" for _, row in df.iterrows()]
    scelta = st.selectbox("🎯 **Seleziona l'azienda specifica per estrarre i dati COMPANY:**", range(len(nomi_aziende)), format_func=lambda x: nomi_aziende[x])
    
    piva_selezionata = df.iloc[scelta].get('piva', df.iloc[scelta].get('id'))
    
    if st.button("📊 ESTRAI DATI CERTIFICATI (Fatturato, PEC, Dipendenti)"):
        with st.spinner("Interrogazione Registro Imprese in corso..."):
            dati_profondi = ottieni_dati_company(piva_selezionata)
            
            if dati_profondi:
                st.markdown("### 📋 Scheda Aziendale Verificata")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Fatturato", f"€ {dati_profondi.get('fatturato', 'N/D')}")
                with c2:
                    st.metric("Dipendenti", dati_profondi.get('numero_dipendenti', 'N/D'))
                with c3:
                    st.metric("Stato", dati_profondi.get('stato_attivita', 'N/D'))

                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**Ragione Sociale:** {dati_profondi.get('denominazione')}")
                    st.write(f"**Partita IVA:** `{dati_profondi.get('piva')}`")
                    st.write(f"**Codice Fiscale:** `{dati_profondi.get('codice_fiscale')}`")
                    st.write(f"**Data Costituzione:** {dati_profondi.get('data_costituzione', 'N/D')}")
                
                with col_info2:
                    st.write(f"**PEC:** `{dati_profondi.get('pec', 'Non disponibile')}`")
                    st.write(f"**Indirizzo:** {dati_profondi.get('indirizzo', '')}, {dati_profondi.get('cap', '')} {dati_profondi.get('comune', '')}")
                    st.write(f"**ATECO:** {dati_profondi.get('codice_ateco', 'N/D')}")

                # Social & Web Search rapida
                st.markdown("---")
                st.markdown("### 🔗 Quick Links")
                ln_nome = dati_profondi.get('denominazione').replace(" ", "%20")
                st.markdown(f"[🔍 Cerca Decision Maker su LinkedIn](https://www.linkedin.com/search/results/people/?keywords={ln_nome})")

    # Tabella riassuntiva di tutti i risultati della ricerca iniziale
    with st.expander("Visualizza lista completa risultati ricerca"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Scarica Lista in CSV", csv, "export_ricerca.csv", "text/csv")

elif st.session_state.query:
    st.warning("Nessun risultato trovato. Prova a cambiare i filtri o il nome.")

#st.sidebar.markdown("""
### Istruzioni
#1. Inserisci il nome azienda.
#2. Clicca su **Cerca**.
#3. Seleziona l'azienda corretta dal menu a tendina.
#4. Clicca su **Estrai Dati** per consumare i crediti Company e vedere PEC e Fatturato.
#""")

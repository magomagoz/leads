import streamlit as st
import pandas as pd
import requests

# --- CONFIGURAZIONE E SESSION STATE ---
st.set_page_config(layout="wide", page_title="Lead Gen CCIAA")

if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None

OPENAPI_KEY = st.secrets.get("OPENAPI_KEY")

if not OPENAPI_KEY:
    st.error("❌ La chiave API non è stata caricata nei Secrets! Aggiungila per continuare.")
    st.stop()
else:
    st.write("✅ Chiave OpenAPI caricata")

st.image("banner.png")
st.info("**Lead Generation** • Dati ufficiali Registro Imprese via OpenAPI.it (V2)")

# --- FUNZIONI API AGGIORNATE ---

@st.cache_data(ttl=3600)
def cerca_aziende_api(nome):
    """Fase 1: Ricerca V2 semplificata"""
    url = "https://company.openapi.com/IT-search"
    headers = {"Authorization": f"Bearer {OPENAPI_KEY}"}
    params = {
        "companyName": nome.strip(),
        # RIMUOVI o commenta la riga dataEnrichment:
        # "dataEnrichment": "Name", 
        "limit": 20
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Estrazione sicura per la V2
            items = data.get("data", data) if isinstance(data, dict) else data
            
            if isinstance(items, list) and len(items) > 0:
                df = pd.DataFrame(items)
                
                # Rinominiamo le nuove colonne V2 per farle leggere alla tua interfaccia
                if 'companyName' in df.columns: df.rename(columns={'companyName': 'denominazione'}, inplace=True)
                if 'vatCode' in df.columns: df.rename(columns={'vatCode': 'piva'}, inplace=True)
                if 'taxCode' in df.columns and 'piva' not in df.columns: df.rename(columns={'taxCode': 'piva'}, inplace=True)
                
                # Gestione della città (nella V2 l'indirizzo arriva strutturato)
                if 'address' in df.columns:
                    df['comune'] = df['address'].apply(lambda x: x.get('city', 'N/D') if isinstance(x, dict) else 'N/D')
                else:
                    df['comune'] = 'N/D'
                    
                return df
        else:
            st.error(f"Errore API {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Errore connessione: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=86400)
def ottieni_dati_company(piva):
    """Fase 2: Recupero dati profondi V2 (IT-advanced)"""
    url = f"https://company.openapi.com/IT-advanced/{piva}"
    headers = {"Authorization": f"Bearer {OPENAPI_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            info = data.get("data", data) if isinstance(data, dict) else data
            
            # Traduciamo i nuovi campi in inglese della V2 nell'italiano della tua UI
            return {
                "denominazione": info.get("companyName", "N/D"),
                "piva": info.get("vatCode", info.get("taxCode", "N/D")),
                "codice_fiscale": info.get("taxCode", "N/D"),
                "pec": info.get("pec", "Non disponibile"),
                "fatturato": info.get("revenue", "N/D"),
                "numero_dipendenti": info.get("employees", "N/D"),
                "stato_attivita": info.get("businessStatus", info.get("companyStatus", "N/D")),
                "indirizzo": info.get("address", {}).get("streetName", "N/D") if isinstance(info.get("address"), dict) else info.get("address", "N/D"),
                "cap": info.get("address", {}).get("zipCode", "") if isinstance(info.get("address"), dict) else "",
                "comune": info.get("address", {}).get("city", "") if isinstance(info.get("address"), dict) else "",
                "codice_ateco": info.get("ateco", {}).get("code", "N/D") if isinstance(info.get("ateco"), dict) else info.get("ateco", "N/D"),
                "data_costituzione": info.get("registrationDate", "N/D")
            }
        else:
            st.error(f"Errore Company API {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Errore connessione Company: {e}")
    return None

# --- INTERFACCIA UTENTE ---

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

if st.session_state.results is not None and not st.session_state.results.empty:
    df = st.session_state.results
    
    st.success(f"✅ Trovate {len(df)} potenziali aziende")
    
    # Adattamento per leggere la PIVA o l'ID della V2
    nomi_aziende = [f"{row['denominazione']} ({row.get('comune', 'N/D')}) - {row.get('piva', row.get('id', 'N/D'))}" for _, row in df.iterrows()]
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

                st.markdown("---")
                st.markdown("### 🔗 Quick Links")
                ln_nome = dati_profondi.get('denominazione').replace(" ", "%20")
                st.markdown(f"[🔍 Cerca Decision Maker su LinkedIn](https://www.linkedin.com/search/results/people/?keywords={ln_nome})")

    with st.expander("Visualizza lista completa risultati ricerca"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Scarica Lista in CSV", csv, "export_ricerca.csv", "text/csv")

elif st.session_state.query:
    st.warning("Nessun risultato trovato. Prova a cambiare i filtri o il nome.")

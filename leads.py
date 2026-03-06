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

    # ... (dopo st.success)
    
    nomi_aziende = []
    # Usiamo una lista di supporto per mappare l'indice alla riga
    for _, row in df.iterrows():
        # Recuperiamo i dati in modo sicuro
        nome = row.get('denominazione') or row.get('companyName') or "Azienda Senza Nome"
        comune = row.get('comune') or "N/D"
        piva = row.get('piva') or row.get('vatCode') or row.get('id') or "N/D"
        
        # Costruiamo la stringa per la selectbox
        nomi_aziende.append(f"{nome} ({comune}) - {piva}")
    
    # Ora passiamo la lista "pulita" al selectbox
    scelta_idx = st.selectbox("🎯 **Seleziona l'azienda specifica:**", range(len(nomi_aziende)), format_func=lambda x: nomi_aziende[x])
    
    # Recuperiamo la riga selezionata in base all'indice (scelta_idx)
    riga_selezionata = df.iloc[scelta_idx]
    
    # Estraiamo la PIVA in modo sicuro
    piva_selezionata = riga_selezionata.get('piva') or riga_selezionata.get('vatCode') or riga_selezionata.get('id')
    
    # ... dopo st.success ...

    # Creiamo la lista per la selectbox in modo sicuro
    nomi_aziende = []
    for _, row in df.iterrows():
        nome = row.get('denominazione') or row.get('companyName') or "Azienda Senza Nome"
        comune = row.get('comune') or "N/D"
        piva = row.get('piva') or row.get('vatCode') or row.get('id') or "N/D"
        nomi_aziende.append(f"{nome} ({comune}) - {piva}")

    # Selectbox unica
    scelta_idx = st.selectbox("🎯 **Seleziona azienda per estrarre dati:**", range(len(nomi_aziende)), format_func=lambda x: nomi_aziende[x])
    
    # Recupero riga e PIVA
    riga_selezionata = df.iloc[scelta_idx]
    piva_selezionata = riga_selezionata.get('piva') or riga_selezionata.get('vatCode') or riga_selezionata.get('id')

    if st.button("📊 ESTRAI DATI CERTIFICATI"):
        with st.spinner("Interrogazione in corso..."):
            dati_profondi = ottieni_dati_company(piva_selezionata)
            
            if dati_profondi:
                # ... (tutto il blocco visualizzazione dati rimane uguale a prima)
                st.markdown("### 📋 Scheda Aziendale Verificata")
                # (Assicurati di mantenere qui i tuoi st.metric e st.write)
                # ...
                
    # Expander finale
    with st.expander("Visualizza lista completa"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Scarica CSV", csv, "export_ricerca.csv", "text/csv")

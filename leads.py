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
    url = "https://company.openapi.com/IT-search"
    headers = {"Authorization": f"Bearer {OPENAPI_KEY}"}
    params = {"companyName": nome.strip(), "limit": 20}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Se la risposta è una lista, usiamola direttamente
            items = data if isinstance(data, list) else data.get("data", [])
            
            if items:
                df = pd.DataFrame(items)
                # Mappiamo i nomi delle colonne per evitare KeyError (usa quello che l'API ti passa davvero)
                # Se i nomi sono diversi da questi, dovremmo vedere cosa c'è dentro df.columns
                colonne_mappa = {
                    'companyName': 'denominazione',
                    'vatCode': 'piva',
                    'taxCode': 'piva'
                }
                df.rename(columns=colonne_mappa, inplace=True)
                return df
    except Exception as e:
        st.error(f"Errore: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=86400)
def ottieni_dati_company(piva):
    url = f"https://company.openapi.com/IT-advanced/{piva}"
    headers = {"Authorization": f"Bearer {OPENAPI_KEY}"}
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code == 200:
        raw_data = response.json()
        # Gestione: se è una lista, prendiamo il primo elemento
        data = raw_data[0] if isinstance(raw_data, list) else raw_data.get("data", raw_data)
        return data if isinstance(data, dict) else {}
    return {}


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

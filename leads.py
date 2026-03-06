import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Hunter")

# --- RECUPERO CHIAVE SICURO ---
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()

# --- HEADER APP ---
st.title("🚀 Lead Generation Avanzata")
st.info("**Powered by Hunter.io & Web Scraping**")

dominio_input = st.text_input("🌐 Inserisci il dominio dell'azienda (es: acea.it, ferrari.com)")

# Pulsante con stile "Primary" (solitamente rosso/arancio nel tema Streamlit)
if st.button("🔎 CERCA CONTATTI E SOCIAL", type="primary"):
    if not dominio_input:
        st.warning("Inserisci un dominio valido prima di cercare.")
    else:
        with st.spinner("Analisi database e scansione sito in corso..."):
            try:
                # 1. Chiamata Hunter.io
                dominio_pulito = dominio_input.strip().lower().replace("https://", "").replace("http://", "").replace("www.", "")
                url_hunter = f"https://api.hunter.io/v2/domain-search?domain={dominio_pulito}&api_key={HUNTER_API_KEY}"
                res = requests.get(url_hunter, timeout=15)
                dati_risposta = res.json()
                data = dati_risposta.get("data", {})
                
                if res.status_code == 200:
                    # 2. Dati base e Scraping di emergenza
                    ragione_sociale = data.get('organization', 'Non trovata')
                    piva_trovata = data.get('vat', 'Non disponibile su Hunter')
                    citta_trovata = data.get('city', 'Non disponibile su Hunter')
                    
                    try:
                        url_sito = f"https://{dominio_pulito}"
                        response_web = requests.get(url_sito, timeout=8)
                        soup = BeautifulSoup(response_web.text, 'html.parser')
                        testo_sito = soup.get_text()

                        if piva_trovata == 'Non disponibile su Hunter':
                            match_piva = re.search(r'\b\d{11}\b', testo_sito)
                            if match_piva: piva_trovata = match_piva.group(0)
                        
                        if citta_trovata == 'Non disponibile su Hunter':
                            match_citta = re.search(r'\d{5}\s+([A-Z][a-z]+)', testo_sito)
                            if match_citta: citta_trovata = match_citta.group(1)
                    except:
                        pass

                    # --- SEZIONE VISUALIZZAZIONE LOGO E INFO ---
                    st.markdown("---")
                    col_logo, col_info = st.columns([1, 4])
                    
                    with col_logo:
                        # FIX: Usiamo 'dominio_pulito' invece di 'dom'
                        logo_url = f"https://logo.clearbit.com/{dominio_pulito}?size=200"
                        try:
                            check_logo = requests.get(logo_url, timeout=5)
                            if check_logo.status_code == 200:
                                st.image(logo_url, width=150)
                            else:
                                st.markdown("### 🏢") 
                        except:
                            st.markdown("### 🏢")
                    
                    with col_info:
                        st.subheader(f"🏢 {ragione_sociale}")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Partita IVA:** {piva_trovata}")
                        with c2:
                            st.write(f"**Città/Sede:** {citta_trovata}")
                            st.write(f"**Sito Web:** [www.{dominio_pulito}](https://{dominio_pulito})")
                    
                    st.markdown("---")

                    # 4. TABELLA PERSONE (Indice da 1)
                    emails = data.get("emails", [])
                    if emails:
                        st.subheader(f"👥 Persone trovate ({len(emails)})")
                        lista = []
                        for e in emails:
                            lista.append({
                                "Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip() or "N/D",
                                "Ruolo": e.get('position', 'N/D'),
                                "Email": e.get('value', 'N/D'),
                                "LinkedIn": e.get('linkedin', 'N/D')
                            })
                        
                        df = pd.DataFrame(lista)
                        df.index = df.index + 1 
                        
                        st.dataframe(df, use_container_width=True, 
                                     column_config={"LinkedIn": st.column_config.LinkColumn()})
                    else:
                        st.warning("Nessun contatto trovato nel database Hunter.")
                else:
                    st.error(f"Errore API Hunter: {dati_risposta.get('errors', [{}])[0].get('detail', 'Errore sconosciuto')}")
            
            except Exception as e:
                st.error(f"Errore critico: {e}")

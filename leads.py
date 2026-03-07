import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Smart Search")

# --- RECUPERO CHIAVE SICURO ---
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()

st.image("banner.png")

#st.title("🚀 Lead Generation Intelligente")
st.info("Inserisci solo il nome (es: 'Acea') e il sistema proverà le estensioni .it, .com, .biz, .eu, .cloud")

nome_input = st.text_input("🏢 Nome azienda o dominio")

if st.button("🔎 AVVIA RICERCA SMART", type="primary"):
    if not nome_input:
        st.warning("Inserisci un nome o un dominio.")
    else:
        with st.spinner("Scansione estensioni in corso..."):
            # Pulizia input e lista estensioni da provare
            nome_puro = nome_input.strip().lower().split('.')[0]
            estensioni = ["it", "com", "biz", "eu", "cloud"]
            
            data_trovata = None
            dominio_vincente = None

            # Ciclo di test sui domini
            for ext in estensioni:
                test_dom = f"{nome_puro}.{ext}"
                url_h = f"https://api.hunter.io/v2/domain-search?domain={test_dom}&api_key={HUNTER_API_KEY}"
                
                try:
                    res = requests.get(url_h, timeout=10)
                    if res.status_code == 200:
                        temp_data = res.json().get("data", {})
                        # Se troviamo almeno una email, consideriamo il dominio valido
                        if temp_data.get("emails"):
                            data_trovata = temp_data
                            dominio_vincente = test_dom
                            break
                except:
                    continue

            if data_trovata:
                # 2. Dati base e Scraping (usando il dominio trovato)
                ragione_sociale = data_trovata.get('organization', nome_puro.capitalize())
                piva_trovata = data_trovata.get('vat', 'Non disponibile su Hunter')
                citta_trovata = data_trovata.get('city', 'Non disponibile su Hunter')
                
                # --- 2. CRAWLING INVESTIGATIVO (HOME + PAGINE CHIAVE) ---
                testo_sito_esteso = ""
                pagine_da_visitare = ["", "/contatti", "/chi-siamo", "/team", "/about-us"]
                
                try:
                    for pag in pagine_da_visitare:
                        url_test = f"https://{dominio_vincente}{pag}"
                        try:
                            res_p = requests.get(url_test, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                            if res_p.status_code == 200:
                                soup_p = BeautifulSoup(res_p.text, 'html.parser')
                                testo_sito_esteso += " " + soup_p.get_text()
                                
                                # Prova a estrarre la città se ancora manca
                                if citta_trovata == 'Non disponibile su Hunter':
                                    # Cerca CAP italiano + Città (es: 00100 Roma)
                                    match_c = re.search(r'\b\d{5}\b\s+([A-Z][a-zA-ZÀ-ÿ\s]+)', soup_p.get_text())
                                    if match_c:
                                        citta_trovata = match_c.group(1).split('\n')[0][:30].strip()
                        except:
                            continue # Se una pagina non esiste, passa alla prossima
                except:
                    pass


                
                    
                # --- VISUALIZZAZIONE ---
                st.success(f"✅ Dominio identificato: **{dominio_vincente}**")
                st.markdown("---")
                col_logo, col_info = st.columns([1, 4])
                
                with col_logo:
                    # (Codice logo precedente...)
                    st.image(f"https://www.google.com/s2/favicons?domain={dominio_vincente}&sz=128", width=80)
                
                with col_info:
                    st.subheader("🏢 Informazioni Aziendali")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**🏭 Ragione Sociale:** {ragione_sociale}")
                        st.write(f"**🆔 Partita IVA:** {piva_trovata}")
                    with c2:
                        st.write(f"**📍 Città/Sede:** {citta_trovata}")
                        st.write(f"**🌐 Sito Web:** www.{dominio_vincente}")

                    # Link rapido a Google Maps per la città
                    if citta_trovata != 'Non disponibile su Hunter':
                        st.caption(f"[Vedi su Maps](https://www.google.com/maps/search/{ragione_sociale}+{citta_trovata})")
                                
                st.markdown("---")

                # --- 4. TABELLA PERSONE CON LINK SOCIAL GENERATI ---
                emails = data_trovata.get("emails", [])
                if emails:
                    st.subheader(f"👥 Persone trovate ({len(emails)})")
                    lista = []
                    for e in emails:
                        #nome_completo = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
    
                        nome = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
                        ruolo = e.get('position', 'N/D')
                        
                        # Se il ruolo è N/D su Hunter, cerchiamo di indovinarlo dal dominio (es. sales@...)
                        email_val = e.get('value', '')
                        if ruolo == 'N/D':
                            if 'sales' in email_val: ruolo = 'Sales Dept'
                            elif 'info' in email_val: ruolo = 'Customer Office'
                            elif 'admin' in email_val: ruolo = 'Administration'

                        linkedin_url = e.get('linkedin')
                        
                        # TRUCCO: Se LinkedIn manca, generiamo un link di ricerca automatica su Google
                        if not linkedin_url and nome_completo:
                            linkedin_url = f"https://www.google.com/search?q=site:linkedin.com/in/+{nome_completo.replace(' ', '+')}+{ragione_sociale}"
                    
                    df = pd.DataFrame(lista)
                    df.index = df.index + 1
                    st.dataframe(df, use_container_width=True, column_config={"🔗 LinkedIn": st.column_config.LinkColumn("Profilo/Ricerca")})

                else:
                    st.warning("Nessun contatto trovato.")

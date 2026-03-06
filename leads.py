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
                
                try:
                    url_sito = f"https://{dominio_vincente}"
                    response_web = requests.get(url_sito, timeout=5)
                    soup = BeautifulSoup(response_web.text, 'html.parser')
                    testo_sito = soup.get_text()
                    if piva_trovata == 'Non disponibile su Hunter':
                        match_piva = re.search(r'\b\d{11}\b', testo_sito)
                        if match_piva: piva_trovata = match_piva.group(0)
                except:
                    pass

                # --- VISUALIZZAZIONE ---
                st.success(f"✅ Dominio identificato: **{dominio_vincente}**")
                st.markdown("---")
                col_logo, col_info = st.columns([1, 4])
                
                with col_logo:
                    logo_url = f"https://logo.clearbit.com/{dominio_vincente}?size=200"
                    st.image(logo_url, width=150)
                
                with col_info:
                    st.subheader("🏢 Informazioni Aziendali")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Ragione Sociale:** {ragione_sociale}")
                        st.write(f"**Partita IVA:** {piva_trovata}")
                    with c2:
                        st.write(f"**Città/Sede:** {citta_trovata}")
                        st.write(f"**Sito Web:** www.{dominio}")
                    
                st.markdown("---")

                # 4. TABELLA PERSONE
                emails = data_trovata.get("emails", [])
                st.subheader(f"👥 Persone trovate ({len(emails)})")
                lista = [{"Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip() or "N/D",
                          "Ruolo": e.get('position', 'N/D'),
                          "Email": e.get('value', 'N/D'),
                          "LinkedIn": e.get('linkedin', 'N/D')} for e in emails]
                
                df = pd.DataFrame(lista)
                df.index = df.index + 1
                st.dataframe(df, use_container_width=True, column_config={"LinkedIn": st.column_config.LinkColumn()})
            else:
                st.error(f"❌ Impossibile trovare dati per '{nome_puro}' con le estensioni comuni.")








                    

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

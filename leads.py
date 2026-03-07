import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# E nel tuo codice sostituisci ogni requests.get con:
session.get(url, timeout=5)

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

nome_input = st.text_input("🏢 **Nome azienda**")

if st.button("🔎 **AVVIA RICERCA SMART**", type="primary"):
    if not nome_input:
        st.warning("Inserisci un nome o un dominio.")
    else:
        with st.spinner("Scansione estensioni in corso..."):
            # Pulizia input e lista estensioni da provare
            nome_puro = nome_input.strip().lower().split('.')[0]
                        # --- POSIZIONE 1: Inizializza qui ---
            progress_bar = st.progress(0)
            
            # Ciclo di test sui domini
            estensioni = ["it", "com", "biz", "eu", "cloud"]
            
            for i, ext in enumerate(estensioni): # Aggiungi 'i' con enumerate
                test_dom = f"{nome_puro}.{ext}"
                url_h = f"https://api.hunter.io/v2/domain-search?domain={test_dom}&api_key={HUNTER_API_KEY}"
                
                try:
                    res = requests.get(url_h, timeout=10)
                    if res.status_code == 200:
                        temp_data = res.json().get("data", {})
                        if temp_data.get("emails"):
                            data_trovata = temp_data
                            dominio_vincente = test_dom
                            # --- POSIZIONE 2: Porta al 100% se trovi subito ---
                            progress_bar.progress(1.0)
                            break
                except:
                    pass
                
                # --- POSIZIONE 3: Aggiorna il progresso ---
                progress_bar.progress((i + 1) / len(estensioni))
               
            # Nasconde la barra una volta finita la ricerca
            progress_bar.empty()


            if data_trovata:
                # 2. Dati base e Scraping (usando il dominio trovato)
                ragione_sociale = data_trovata.get('organization', nome_puro.capitalize())
                #piva_trovata = data_trovata.get('vat', 'Non disponibile su Hunter')
                
                # --- SCRAPING AVANZATO P.IVA ---
                piva_trovata = data_trovata.get('vat') or "Non trovata"
                
                if piva_trovata == "Non trovata":
                    pagine_target = ["", "/contatti", "/chi-siamo", "/legal", "/privacy-policy"]
                    
                    # Pattern P.IVA: cerca 11 cifre, anche separate da spazi o punti
                    regex_piva = r'(?:P\.?\s*I\.?\s*V\.?\s*A\.?\s*[:\s]*|VAT\s*[:\s]*|Partita\s*IVA\s*[:\s]*)\s*(\d[.\s\d]{10,13}\d)'
                    
                    for pag in pagine_target:
                        try:
                            res = requests.get(f"https://{dominio_vincente}{pag}", timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                            if res.status_code == 200:
                                # Cerchiamo il pattern nel testo
                                match = re.search(regex_piva, res.text, re.IGNORECASE)
                                if match:
                                    # Pulizia stringa trovata (togliamo punti e spazi)
                                    piva_pulita = re.sub(r'[\s.]', '', match.group(1))
                                    piva_trovata = piva_pulita
                                    break # Trovata, fermiamo la ricerca
                        except:
                            continue

                citta_trovata = data_trovata.get('city', 'Non disponibile su Hunter')
                
                # --- 2. CRAWLING INVESTIGATIVO (HOME + PAGINE CHIAVE) ---
                testo_sito_esteso = ""
                
                pagine_da_visitare = ["/contatti", "/chi-siamo"] # Limitiamo le pagine critiche
                
                for pag in pagine_da_visitare:
                    if citta_trovata != 'Non disponibile su Hunter': # Se l'abbiamo già, non cercare più
                        break
                        
                    url_test = f"https://{dominio_vincente}{pag}"
                    try:
                        res_p = session.get(url_test, timeout=3) # Timeout più stretto
                        if res_p.status_code == 200:
                            soup_p = BeautifulSoup(res_p.text, 'html.parser')
                            # Regex ottimizzata per estrarre la città
                            match_c = re.search(r'\b\d{5}\b\s+([A-Z][a-zA-ZÀ-ÿ\s]{2,20})', soup_p.get_text())
                            if match_c:
                                citta_trovata = match_c.group(1).strip()
                    except:
                        continue
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

                # --- 4. TABELLA PERSONE CON "LINKEDIN MAGIC SEARCH" ---
                emails = data_trovata.get("emails", [])
                if emails:
                    st.subheader(f"👥 Lead Identificati ({len(emails)})")
                    lista = []
                    for e in emails:
                        nome = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
                        ruolo = e.get('position', 'N/D')
                        
                        # Se il ruolo è N/D su Hunter, cerchiamo di indovinarlo dal dominio (es. sales@...)
                        email_val = e.get('value', '')
                        if ruolo == 'N/D':
                            if 'sales' in email_val: ruolo = 'Sales Dept'
                            elif 'info' in email_val: ruolo = 'Customer Office'
                            elif 'admin' in email_val: ruolo = 'Administration'
                        
                        # GENERAZIONE LINK LINKEDIN (Cerca su Google se manca il link diretto)
                        lk_url = e.get('linkedin')
                        if not lk_url and nome:
                            # Ricerca mirata: site:linkedin.com/in/ Nome Cognome Azienda
                            lk_url = f"https://www.google.com/search?q=site:linkedin.com/in/+{nome.replace(' ', '+')}+{ragione_sociale.replace(' ', '+')}"
                        
                        lista.append({
                            "👤 Nome": nome or "Lead",
                            "💼 Ruolo": ruolo,
                            "📧 Email": email_val,
                            "🔗 LinkedIn": lk_url
                        })
                    
                    df = pd.DataFrame(lista)
                    df.index = df.index + 1
                    
                    # Colonna LinkedIn come Link cliccabile
                    st.dataframe(df, use_container_width=True, 
                                 column_config={"🔗 LinkedIn": st.column_config.LinkColumn("Apri Profilo/Ricerca")})
                else:
                    st.warning("Nessun contatto trovato.")


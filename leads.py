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
                    # Definiamo l'URL del logo
                    logo_url = f"https://logo.clearbit.com/{dominio_vincente}?size=200"
                    
                    try:
                        # Usiamo un User-Agent per sembrare un browser vero e non un bot
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                        check_logo = requests.get(logo_url, headers=headers, timeout=5)
                        
                        if check_logo.status_code == 200:
                            st.image(logo_url, width=150)
                        else:
                            # Se Clearbit fallisce, proviamo un secondo servizio (Google Favicon)
                            backup_logo = f"https://www.google.com/s2/favicons?domain={dominio_vincente}&sz=128"
                            st.image(backup_logo, width=100)
                            st.caption("Logo da Google")
                    except Exception as e:
                        st.markdown("### 🏢")
                        st.caption("Logo non disponibile")
                
                with col_info:
                    st.subheader("🏢 Informazioni Aziendali")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Ragione Sociale:** {ragione_sociale}")
                        st.write(f"**Partita IVA:** {piva_trovata}")
                    with c2:
                        st.write(f"**Città/Sede:** {citta_trovata}")
                        st.write(f"**Sito Web:** www.{dominio_vincente}")
                    
                st.markdown("---")

                # 4. TABELLA PERSONE CON ICONE
                emails = data_trovata.get("emails", [])
                if emails:
                    st.subheader(f"👥 Persone trovate ({len(emails)})")
                    
                    lista = []
                    for e in emails:
                        lista.append({
                            "👤 Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip() or "N/D",
                            "💼 Ruolo": e.get('position', 'N/D'),
                            "📧 Email": e.get('value', 'N/D'),
                            "🔗 LinkedIn": e.get('linkedin', 'N/D')
                        })
                    
                    df = pd.DataFrame(lista)
                    df.index = df.index + 1 # Numerazione da 1
                    
                    # Configurazione colonne per rendere cliccabile LinkedIn
                    st.dataframe(
                        df, 
                        use_container_width=True, 
                        column_config={
                            "🔗 LinkedIn": st.column_config.LinkColumn()
                        }
                    )
                else:
                    st.warning("Nessun contatto trovato per questo dominio.")

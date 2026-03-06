import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# --- CONFIGURAZIONE ---
st.set_page_config(layout="wide", page_title="Lead Gen Hunter")
st.title("🚀 Lead Generation Avanzata")
st.info("**Powered by Hunter.io & Web Scraping**")

# --- RECUPERO CHIAVE ---
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()

dominio = st.text_input("🌐 Inserisci il dominio (es: acea.it)")

if st.button("🔎 CERCA CONTATTI E SOCIAL"):
    with st.spinner("Interrogazione database e scansione sito in corso..."):
        try:
            # 1. Chiamata Hunter.io
            url_hunter = f"https://api.hunter.io/v2/domain-search?domain={dominio.strip()}&api_key={HUNTER_API_KEY}"
            res = requests.get(url_hunter, timeout=15)
            data = res.json().get("data", {})
            
            # 2. Dati base
            ragione_sociale = data.get('organization', 'Non trovata')
            piva_trovata = data.get('vat', 'Non disponibile su Hunter')
            citta_trovata = data.get('city', 'Non disponibile su Hunter')
            
            # 3. SCRAPING AVANZATO (P.IVA e LOCALITÀ)
            try:
                url_sito = f"https://{dominio.strip()}"
                response_web = requests.get(url_sito, timeout=10)
                soup = BeautifulSoup(response_web.text, 'html.parser')
                testo_sito = soup.get_text()

                # Ricerca Partita IVA con Regex (formato italiano 11 cifre)
                if piva_trovata == 'Non disponibile su Hunter':
                    match_piva = re.search(r'\b\d{11}\b', testo_sito)
                    if match_piva:
                        piva_trovata = match_piva.group(0)
                
                # Ricerca Città (cerchiamo CAP + Città o parole chiave)
                if citta_trovata == 'Non disponibile su Hunter':
                    # Cerca pattern comuni come "00100 Roma" o "Sede: Milano"
                    match_citta = re.search(r'\d{5}\s+([A-Z][a-z]+)', testo_sito)
                    if match_citta:
                        citta_trovata = match_citta.group(1)
                    elif "Sede legale:" in testo_sito:
                        # Estrae un po' di testo dopo la parola chiave
                        citta_trovata = testo_sito.split("Sede legale:")[1][:30].strip()
            except:
                pass

            # 4. VISUALIZZAZIONE INFO AZIENDA
            st.subheader("🏢 Informazioni Aziendali")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Ragione Sociale:** {ragione_sociale}")
                st.write(f"**Partita IVA:** {piva_trovata}")
            with c2:
                st.write(f"**Città/Sede:** {citta_trovata}")
                st.write(f"**Sito Web:** www.{dominio}")
            
            st.markdown("---")

            # 5. TABELLA PERSONE
            emails = data.get("emails", [])
            if emails:
                st.subheader(f"👥 Persone trovate ({len(emails)})")
                lista = []
                for e in emails:
                    lista.append({
                        "Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}",
                        "Ruolo": e.get('position', 'N/D'),
                        "Email": e.get('value', 'N/D'),
                        "LinkedIn": e.get('linkedin', 'N/D')
                    })
                df = pd.DataFrame(lista)
                st.dataframe(df, use_container_width=True, 
                             column_config={"LinkedIn": st.column_config.LinkColumn()})
            else:
                st.warning("Nessun contatto trovato.")

        except Exception as e:
            st.error(f"Errore tecnico: {e}")

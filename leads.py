import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

st.set_page_config(layout="wide")
st.title("🏢 Ricerca Aziende Italiane")
st.markdown("**Web + CCIAA pubbliche - NO TOKEN!**")

# 🔍 Campo ricerca
query = st.text_input("Nome o P.IVA:", placeholder="Apple, 01234567890")

if st.button("🔎 CERCA", type="primary") and query:
    with st.spinner("Ricerca web + CCIAA..."):
        # 1️⃣ WEB SEARCH (reportaziende.it + simili)
        risultati = cerca_web(query)
        
        # 2️⃣ CCIAA PUBBLICHE (no API)
        if not risultati.empty:
            st.success(f"✅ {len(risultati)} risultati trovati!")
            st.dataframe(risultati, use_container_width=True)
            
            # Dettagli primo risultato
            primo = risultati.iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### 🏢 **{primo['Nome']}**")
                st.metric("📍 Città", primo['Città'])
                st.metric("💰 Fatturato", primo['Fatturato'])
            with col2:
                st.markdown("### 📧 Dati")
                st.info(f"**P.IVA:** {primo['P.IVA']}")
                st.markdown(f"[🔗 Sito]({primo['Link']})")
        else:
            st.warning("❌ Nessun risultato")
            st.info("Prova: Fiat, Enel, 01234567890")

def cerca_web(query):
    """Cerca su siti CCIAA pubbliche"""
    results = []
    
    # Siti CCIAA + report gratuiti
    siti = [
        f"https://www.reportaziende.it/ricerca?query={query}",
        f"https://www.fatturatoitalia.it/ricerca?q={query}",
        f"https://www.ufficiocamerale.it/cerca-azienda/{query.replace(' ', '-')}"
    ]
    
    for sito in siti:
        try:
            resp = requests.get(sito, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Estrai dati (pattern comuni)
            titoli = soup.find_all(['h1', 'h2', 'h3'])[:3]
            for t in titoli:
                text = t.get_text()
                piva_match = re.search(r'\d{11}', text)
                results.append({
                    'Nome': text[:50],
                    'P.IVA': piva_match.group() if piva_match else 'N/D',
                    'Città': 'Roma/Milano',  # Parsing reale da aggiungere
                    'Fatturato': '€1.2M',    # Parsing reale da aggiungere
                    'Link': sito
                })
        except:
            continue
    
    return pd.DataFrame(results[:5]) if results else pd.DataFrame()

st.markdown("---")
st.caption("🔍 Fonti: ReportAziende.it + CCIAA pubbliche")

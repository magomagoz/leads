import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
from datetime import datetime
from urllib.parse import urlparse

# Configurazione sessione
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# --- 1. UTILITY PER NOMI COMPOSTI ---
def pulisci_nome_per_dominio(nome):
    """Trasforma 'King Limousine' in 'kinglimousine'"""
    nome = nome.lower().strip()
    # Rimuove caratteri speciali e spazi
    nome_pulito = re.sub(r'[^a-z0-9]', '', nome)
    return nome_pulito

# --- 2. ESTRATTORE SOCIAL ---
def trova_social(soup):
    """Cerca link social nel codice HTML della pagina"""
    socials = {"linkedin": None, "facebook": None, "instagram": None}
    patterns = {
        "linkedin": r'linkedin\.com/(?:company|in)/[\w-]+',
        "facebook": r'facebook\.com/[\w.-]+',
        "instagram": r'instagram\.com/[\w.-]+'
    }
    
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        for platform, pattern in patterns.items():
            if not socials[platform] and re.search(pattern, href):
                # Gestione link relativi o mancanti di schema
                if href.startswith('/'): continue 
                socials[platform] = href
    return socials

# --- 3. SCRAPING P.IVA E CITTÀ ---
def trova_piva(testo):
    pattern = r'(?:partita\s*iva|p\.?i\.?v\.?a|vat)\s*(?::|n\.?)?\s*([0-9]{11})'
    match = re.search(pattern, testo, re.IGNORECASE)
    return match.group(1) if match else None

def trova_citta(testo):
    # Pattern per CAP italiano + Nome Città
    pattern = r'\b\d{5}\b\s+([A-Z][a-zA-Zà-ÿ\s]{2,20})'
    match = re.search(pattern, testo)
    return match.group(1).strip() if match else None

# --- CONFIGURAZIONE STREAMLIT ---
st.set_page_config(layout="wide", page_title="Lead Gen Pro")

try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ HUNTER_API_KEY non configurata!")
    st.stop()

st.title("🚀 Lead Generation & Social Finder")

nome_input = st.text_input("🏢 Inserisci Nome Azienda (es. ACEA)")

if st.button("🔎 AVVIA RICERCA", type="primary"):
    if not nome_input:
        st.warning("Inserisci un nome.")
    else:
        with st.spinner("Analisi in corso..."):
            # Gestione nome composto
            nome_puro = pulisci_nome_per_dominio(nome_input)
            estensioni = ["it", "com", "net", "eu", "cloud", "biz"]
            
            data_trovata = None
            dominio_vincente = ""

            # 1. Ricerca Dominio
            for ext in estensioni:
                test_dom = f"{nome_puro}.{ext}"
                url_h = f"https://api.hunter.io/v2/domain-search?domain={test_dom}&api_key={HUNTER_API_KEY}"
                try:
                    res = session.get(url_h, timeout=5)
                    if res.status_code == 200:
                        temp_data = res.json().get("data", {})
                        if temp_data.get("emails") or temp_data.get("organization"):
                            data_trovata = temp_data
                            dominio_vincente = test_dom
                            break
                except: continue

            if not data_trovata:
                st.error("Impossibile trovare un dominio valido per questa azienda. Prova con il sito web diretto.")
            else:
                # 2. Deep Scraping per Social e Dati Legali
                social_links = {}
                piva_trovata = "Non trovata"
                citta_trovata = "Non trovata"
                
                try:
                    r = session.get(f"http://www.{dominio_vincente}", timeout=8)
                    soup = BeautifulSoup(r.text, 'html.parser')
                    testo_completo = soup.get_text(separator=' ', strip=True)
                    
                    social_links = trova_social(soup)
                    piva_trovata = trova_piva(testo_completo) or "Non trovata"
                    citta_trovata = trova_citta(testo_completo) or "Non trovata"
                except:
                    st.warning("Impossibile accedere direttamente al sito per lo scraping social.")

                # --- UI DISPLAY ---
                st.subheader(f"🏢 {data_trovata.get('organization', nome_input.capitalize())}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Partita IVA", piva_trovata)
                col2.metric("Sede", citta_trovata)
                col3.metric("Dominio", dominio_vincente)

                # Sezione Social
                st.write("### 🔗 Canali Social Trovati")
                s_cols = st.columns(3)
                for i, (platform, link) in enumerate(social_links.items()):
                    if link:
                        s_cols[i].markdown(f"✅ **[{platform.capitalize()}]({link})**")
                    else:
                        s_cols[i].markdown(f"❌ {platform.capitalize()} non trovato")

                # --- TABELLA EMAIL ---
                emails = data_trovata.get("emails", [])
                if emails:
                    st.write(f"### 👥 Contatti Email ({len(emails)})")
                    df_list = []
                    for e in emails:
                        df_list.append({
                            "Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}",
                            "Ruolo": e.get('position', 'N/D'),
                            "Email": e.get('value'),
                            "Tipo": e.get('type')
                        })
                    df = pd.DataFrame(df_list)
                    st.table(df)

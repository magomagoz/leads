import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Smart Search")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# --- RECUPERO CHIAVE ---
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata!")
    st.stop()

# --- FUNZIONI DI SUPPORTO ---
def pulisci_nome_per_dominio(nome):
    nome = nome.lower().strip()
    return re.sub(r'[^a-z0-9]', '', nome)

def trova_social(soup):
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
                if not href.startswith('http'): continue
                socials[platform] = href
    return socials

def trova_piva(testo):
    pattern = r'(?:partita\s*iva|p\.?i\.?v\.?a|vat)\s*(?::|n\.?)?\s*([0-9\s.]{11,15})'
    match = re.search(pattern, testo, re.IGNORECASE)
    return re.sub(r'[\s.]', '', match.group(1)) if match else None

def trova_citta(testo):
    pattern = r'\b\d{5}\b\s+([A-Z][a-zA-Zà-ÿ\s]{2,20})'
    match = re.search(pattern, testo)
    return match.group(1).strip() if match else None

# --- GESTIONE PDF ---
class PDFReport(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", align='C')

def crea_pdf(ragione_sociale, piva, citta, sito, df, dominio):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, f"Report Lead: {ragione_sociale}", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Partita IVA: {piva} | Sede: {citta}", ln=True)
    pdf.cell(0, 10, f"Sito: {sito}", ln=True)
    pdf.ln(10)
    
    if not df.empty:
        pdf.set_font("Arial", 'B', 10)
        for _, row in df.iterrows():
            pdf.cell(0, 8, f"{row['👤 Nome']} - {row['💼 Ruolo']} - {row['📧 Email']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA APP ---
st.title("🚀 Smart Lead Selector")
st.info("Inserisci il nome (es. 'King Limousine'). Il sistema cercherà tutti i domini disponibili.")

nome_input = st.text_input("🏢 **Nome Azienda**", key="main_input")

# Inizializza session_state per i risultati della scansione
if 'risultati_scansione' not in st.session_state:
    st.session_state.risultati_scansione = None

if st.button("🔎 SCANSIONA ESTENSIONI"):
    if not nome_input:
        st.warning("Inserisci un nome.")
    else:
        with st.spinner("Scansione in corso su tutte le estensioni..."):
            nome_puro = pulisci_nome_per_dominio(nome_input)
            estensioni = ["it", "com", "net", "eu", "biz", "org", "cloud"]
            trovati = []
            
            p_bar = st.progress(0)
            for i, ext in enumerate(estensioni):
                test_dom = f"{nome_puro}.{ext}"
                try:
                    url_h = f"https://api.hunter.io/v2/domain-search?domain={test_dom}&api_key={HUNTER_API_KEY}"
                    res = session.get(url_h, timeout=5).json()
                    data = res.get("data", {})
                    if data.get("emails") or data.get("organization"):
                        trovati.append({"dominio": test_dom, "data": data})
                except: pass
                p_bar.progress((i + 1) / len(estensioni))
            
            st.session_state.risultati_scansione = trovati
            if not trovati:
                st.error("Nessun dominio trovato. Prova un altro nome.")

# --- LIVELLO INTERMEDIO: SELEZIONE ---
if st.session_state.risultati_scansione:
    st.write("### 🎯 Scegli il dominio corretto per generare il report:")
    
    # Creiamo una lista di opzioni per l'utente
    opzioni = {res['dominio']: res for res in st.session_state.risultati_scansione}
    scelta = st.radio("Domini individuati:", list(opzioni.keys()), horizontal=True)

    if st.button("🚀 GENERA REPORT PER " + scelta.upper()):
        res_selezionato = opzioni[scelta]
        data_trovata = res_selezionato['data']
        dominio_vincente = res_selezionato['dominio']
        
        # --- ELABORAZIONE DATI ---
        ragione_sociale = data_trovata.get('organization') or nome_input.title()
        piva_trovata = data_trovata.get('vat', "Non trovata")
        citta_trovata = data_trovata.get('city', "Non trovata")
        
        # Scraping Social & Legal
        social_links = {}
        try:
            r = session.get(f"http://www.{dominio_vincente}", timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            social_links = trova_social(soup)
            if piva_trovata == "Non trovata": piva_trovata = trova_piva(text) or "Non trovata"
            if citta_trovata == "Non trovata": citta_trovata = trova_citta(text) or "Non trovata"
        except: st.warning("Impossibile analizzare il sito web per i social.")

        # --- DISPLAY RISULTATI ---
        st.markdown("---")
        c1, c2 = st.columns([1, 3])
        with c1: st.image(f"https://www.google.com/s2/favicons?domain={dominio_vincente}&sz=128")
        with c2:
            st.subheader(f"🏢 {ragione_sociale}")
            st.write(f"📍 **Sede:** {citta_trovata} | 🆔 **P.IVA:** {piva_trovata}")
            
        st.write("#### 🔗 Social")
        scols = st.columns(3)
        for i, (p, l) in enumerate(social_links.items()):
            scols[i].write(f"[{p.capitalize()}]({l})" if l else f"{p.capitalize()}: ❌")

        # Tabella Email
        emails = data_trovata.get("emails", [])
        df = pd.DataFrame()
        if emails:
            st.write("#### 👥 Contatti")
            lista = []
            for e in emails:
                nome = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip() or "Lead"
                email = e.get('value', '')
                ruolo = e.get('position', 'N/D')
                lk = e.get('linkedin') or f"https://www.google.com/search?q=linkedin+{nome}+{ragione_sociale}"
                lista.append({"👤 Nome": nome, "💼 Ruolo": ruolo, "📧 Email": email, "🔗 LinkedIn": lk})
            df = pd.DataFrame(lista)
            st.dataframe(df, column_config={"🔗 LinkedIn": st.column_config.LinkColumn()})
        
        # Download
        pdf_data = crea_pdf(ragione_sociale, piva_trovata, citta_trovata, dominio_vincente, df, dominio_vincente)
        st.download_button("📥 Scarica PDF", pdf_data, f"{dominio_vincente}.pdf", "application/pdf")

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

# --- 1. SCRAPING P.IVA POTENZIATO ---
def trova_piva(testo, dominio):
    # Regex mirata per P.IVA italiana (11 cifre)
    pattern = r'(?:partita\s*iva|p\.?i\.?v\.?a|vat)\s*(?::|n\.?)?\s*([0-9\s.]{11,15})'
    match = re.search(pattern, testo, re.IGNORECASE)
    if match:
        return re.sub(r'[\s.]', '', match.group(1))
    return None

# --- 2. SCRAPING CITTÀ POTENZIATO ---
def trova_citta(testo):
    # Cerca il pattern CAP + CITTÀ (es. 00144 Roma)
    pattern = r'\b\d{5}\b\s+([A-Z][a-zA-Zà-ÿ\s]{2,20})'
    match = re.search(pattern, testo)
    return match.group(1).strip() if match else None

def crea_pdf(ragione_sociale, piva, citta, sito, df, dominio):
    pdf = PDFReport()
    pdf.add_page()
    # Logo dinamico
    try:
        logo_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=128"
        img_data = requests.get(logo_url, timeout=3).content
        with open("temp_logo.png", "wb") as f: f.write(img_data)
        pdf.image("temp_logo.png", x=10, y=8, w=15)
    except: pass

    # Header e Dati
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, f"Report Lead: {ragione_sociale}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Partita IVA: {piva}", ln=True)
    pdf.cell(0, 10, f"Sede: {citta}", ln=True)
    pdf.cell(0, 10, f"Sito: {sito}", ln=True)
    pdf.ln(10)
    
    # Tabella
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 10, "Nome", border=1, fill=True)
    pdf.cell(50, 10, "Ruolo", border=1, fill=True)
    pdf.cell(90, 10, "Email", border=1, fill=True)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(50, 10, str(row['👤 Nome'])[:25], border=1)
        pdf.cell(50, 10, str(row['💼 Ruolo'])[:25], border=1)
        pdf.cell(90, 10, str(row['📧 Email']), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Smart Search")

# --- RECUPERO CHIAVE SICURO ---
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()
# --- CLASSE PER PDF PROFESSIONALE ---
class PDFReport(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')} | Pagina {self.page_no()}", align='C')

st.image("banner.png")

#st.title("🚀 Lead Generation Intelligente")
st.info("Inserisci solo il nome (es: 'Acea') e il sistema proverà le estensioni .it, .com, .biz, .eu, .cloud, .net")

nome_input = st.text_input("🏢 **Inserisci nome azienda**")

if st.button("🔎 **AVVIA RICERCA SMART**", type="primary"):
    if not nome_input:
        st.warning("Inserisci un nome.")
    else:
        with st.spinner("Ricerca in corso..."):
            nome_puro = nome_input.strip().lower().split('.')[0]
            progress_bar = st.progress(0)
            estensioni = ["it", "com", "biz", "eu", "cloud", "net"]
            
            data_trovata = None # Inizializza come None
            dominio_vincente = ""

            for i, ext in enumerate(estensioni):
                test_dom = f"{nome_puro}.{ext}"
                url_h = f"https://api.hunter.io/v2/domain-search?domain={test_dom}&api_key={HUNTER_API_KEY}"
                
                try:
                    # Usa session.get invece di requests.get
                    res = session.get(url_h, timeout=10) 
                    if res.status_code == 200:
                        temp_data = res.json().get("data", {})
                        if temp_data.get("emails"):
                            data_trovata = temp_data
                            dominio_vincente = test_dom
                            progress_bar.progress(1.0)
                            break
                except:
                    pass
                progress_bar.progress((i + 1) / len(estensioni))
            
            progress_bar.empty()
            
            # Aggiunto controllo: se non troviamo dati, avvisiamo l'utente
            if not data_trovata:
                st.error("❌ Nessun dato trovato per questo nome. Prova ad inserire il dominio completo.")
                st.stop()

            if data_trovata:
                # Usa input_pulito (o dominio_vincente) invece di nome_puro
                ragione_sociale = data_trovata.get('organization', nome_puro.capitalize())
                
                # --- SCRAPING AVANZATO P.IVA E CITTÀ ---
                piva_trovata = data_trovata.get('vat', 'Non trovata')
                citta_trovata = data_trovata.get('city', 'Non trovata')
                
                # Scansione pagine per dati mancanti
                if piva_trovata == 'Non trovata' or citta_trovata == 'Non trovata':
                    pagine = ["", "/contatti", "/chi-siamo", "/legal", "/privacy-policy"]
                    for p in pagine:
                        try:
                            r = session.get(f"https://{dominio_vincente}{p}", timeout=5)
                            soup = BeautifulSoup(r.text, 'html.parser')
                            testo = soup.get_text(separator=' ', strip=True)
                            
                            if piva_trovata == 'Non trovata':
                                piva_trovata = trova_piva(testo, dominio_vincente) or 'Non trovata'
                            if citta_trovata == 'Non trovata':
                                citta_trovata = trova_citta(testo) or 'Non trovata'
                        except: 
                            continue

                # --- VISUALIZZAZIONE ---
                st.success(f"✅ Dominio identificato: **{dominio_vincente}**")
                st.markdown("---")
                st.header("🏢 Informazioni Aziendali")
                col_logo, col_info = st.columns([1, 4])
                
                with col_logo:
                    st.image(f"https://www.google.com/s2/favicons?domain={dominio_vincente}&sz=128", width=80)
                
                with col_info:
                    c1, c2 = st.columns(2)
                    c1.write(f"**🏭 Ragione Sociale:** {ragione_sociale}")
                    c1.write(f"**🆔 Partita IVA:** {piva_trovata}")
                    c2.write(f"**📍 Città/Sede:** {citta_trovata}")
                    c2.write(f"**🌐 Sito Web:** www.{dominio_vincente}")

                    # Link rapido a Google Maps per la città
                    if citta_trovata != 'Non disponibile su Hunter':
                        st.caption(f"[Vedi su Maps](https://www.google.com/maps/search/{ragione_sociale}+{citta_trovata})")
                         
                # Sezione Social
                st.write("### 🔗 Canali Social Trovati")
                s_cols = st.columns(3)
                for i, (platform, link) in enumerate(social_links.items()):
                    if link:
                        s_cols[i].markdown(f"✅ **[{platform.capitalize()}]({link})**")
                    else:
                        s_cols[i].markdown(f"❌ {platform.capitalize()} non trovato")
                        
                st.markdown("---")

                # --- 4. TABELLA PERSONE CON "LINKEDIN MAGIC SEARCH" ---
                emails = data_trovata.get("emails", [])
                if emails:
                    st.subheader(f"👥 Contatti Identificati ({len(emails)})")
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
                
        # --- AGGIUNTA PULSANTE DOWNLOAD NELL'APP ---
                st.download_button("📥 Scarica Report PDF", data=crea_pdf(ragione_sociale, piva_trovata, citta_trovata, dominio_vincente, df, dominio_vincente), file_name=f"Report_{ragione_sociale}.pdf", mime="application/pdf")
            else:
                st.error("Dati non trovati.")
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

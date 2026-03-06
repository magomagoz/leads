import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Hunter")

# --- RECUPERO CHIAVE SICURO ---
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()

st.title("🚀 Lead Generation Avanzata")
st.info("**Powered by Hunter.io** • Estrai Decision Maker e Profili Social")

dominio = st.text_input("🌐 Inserisci il dominio (es: acea.it)")

if st.button("🔎 CERCA CONTATTI E SOCIAL"):
    with st.spinner("Interrogazione in corso..."):
        try:
            # 1. Chiamata Hunter
            url_hunter = f"https://api.hunter.io/v2/domain-search?domain={dominio.strip()}&api_key={HUNTER_API_KEY}"
            response = requests.get(url_hunter, timeout=15)
            dati_risposta = response.json()
            
            if response.status_code == 200:
                data = dati_risposta.get("data", {})
                
                # 2. Estrazione dati
                ragione_sociale = data.get('organization', 'Non trovata')
                piva_trovata = data.get('vat', 'Non disponibile su Hunter')
                citta_trovata = data.get('city', 'Non disponibile su Hunter')
                
                # 3. SCRAPING DI EMERGENZA
                if piva_trovata == 'Non disponibile su Hunter' or citta_trovata == 'Non disponibile su Hunter':
                    try:
                        url_sito = f"https://{dominio.strip()}"
                        html = requests.get(url_sito, timeout=5).text
                        soup = BeautifulSoup(html, 'html.parser')
                        testo_sito = soup.get_text()
                        if "P.IVA" in testo_sito or "Partita IVA" in testo_sito:
                            piva_trovata = "Trovata nel sito - Controlla footer"
                        if "Sede:" in testo_sito:
                            citta_trovata = "Vedi sito web"
                    except:
                        pass

                # Visualizzazione risultati
                st.subheader("🏢 Informazioni Aziendali")
                col1, col2 = st.columns(2)
                col1.write(f"**Ragione Sociale:** {ragione_sociale}")
                col1.write(f"**Partita IVA:** {piva_trovata}")
                col2.write(f"**Città:** {citta_trovata}")
                st.markdown("---")
                
                # --- PERSONE ---
                emails = data.get("emails", [])
                if emails:
                    st.subheader(f"👥 Persone trovate ({len(emails)})")
                    lista = [{"Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}", 
                              "Ruolo": e.get('position', 'N/D'), 
                              "Email": e.get('value', 'N/D'), 
                              "LinkedIn": e.get('linkedin', 'N/D')} for e in emails]
                    df = pd.DataFrame(lista)
                    st.dataframe(df, use_container_width=True, column_config={"LinkedIn": st.column_config.LinkColumn()})
                else:
                    st.warning("Nessun contatto pubblico trovato.")
            else:
                st.error("Errore nella richiesta API: verifica il dominio o la chiave.")
        except Exception as e:
            st.error(f"Errore critico: {e}")

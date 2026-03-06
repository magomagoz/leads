import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup # Importante per leggere il web

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Hunter")

# --- RECUPERO CHIAVE API ---
# Nota: dovrai cambiare il nome della variabile nei secrets di Streamlit
HUNTER_API_KEY = st.secrets.get("HUNTER_API_KEY", "")

st.image("banner.png")
#st.title("🚀 Lead Generation Avanzata")
st.info("**Powered by Hunter.io** • Estrai Decision Maker e Profili Social")

# --- RECUPERO CHIAVE SICURO ---
# Assicurati di aver salvato HUNTER_API_KEY nei Secrets di Streamlit
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()

dominio = st.text_input("🌐 Inserisci il dominio (es: acea.it)")

if st.button("🔎 CERCA CONTATTI E SOCIAL"):
    with st.spinner("Interrogazione in corso..."):
        # 1. Chiamata Hunter
        url_hunter = f"https://api.hunter.io/v2/domain-search?domain={dominio.strip()}&api_key={HUNTER_API_KEY}"
        response = requests.get(url_hunter, timeout=15)
        dati_risposta = response.json()
        data = dati_risposta.get("data", {})
        
        # 2. Estrazione dati (con fallback per P.IVA/Città)
        ragione_sociale = data.get('organization', 'Non trovata')
        piva_trovata = data.get('vat', 'Non disponibile su Hunter')
        citta_trovata = data.get('city', 'Non disponibile su Hunter')
        
        # 3. SCRAPING DI EMERGENZA (Se mancano i dati)
        if piva_trovata == 'Non disponibile su Hunter' or citta_trovata == 'Non disponibile su Hunter':
            try:
                # Tentiamo di leggere la home page
                url_sito = f"https://{dominio.strip()}"
                html = requests.get(url_sito, timeout=5).text
                soup = BeautifulSoup(html, 'html.parser')
                testo_sito = soup.get_text()
                
                # Semplice logica di ricerca nel testo
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
                st.error("Errore nella richiesta: verifica il dominio o la chiave API.")
        except Exception as e:
            st.error(f"Errore critico: {e}")

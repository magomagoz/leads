import streamlit as st
import requests
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Hunter")

# --- RECUPERO CHIAVE API ---
# Nota: dovrai cambiare il nome della variabile nei secrets di Streamlit
HUNTER_API_KEY = st.secrets.get("HUNTER_API_KEY", "")

st.title("🚀 Lead Generation Avanzata")
st.info("**Powered by Hunter.io** • Estrai Sede, Decision Maker e Profili Social")

if not HUNTER_API_KEY:
    st.error("❌ Manca la chiave HUNTER_API_KEY nei Secrets di Streamlit!")
    st.stop()
else:
    st.success("✅ Chiave API Hunter caricata")

st.markdown("---")

# --- INTERFACCIA DI RICERCA ---
# Per Apollo, la ricerca per dominio del sito web è la più precisa
dominio_input = st.text_input("🌐 **Inserisci il dominio web dell'azienda**", 
                              placeholder="Es: acea.it, eni.com, ferrari.com...")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    btn_cerca = st.button("🔎 CERCA CONTATTI E SOCIAL", type="primary", use_container_width=True)
with col_btn2:
    if st.button("🗑️ RESET", use_container_width=True):
        st.rerun()

st.markdown("---")

# Sostituisci il blocco della ricerca con questo:
if btn_cerca and dominio_input:
    with st.spinner(f"Ricerca contatti su Hunter.io per {dominio_input}..."):
        # Endpoint di Hunter.io
        url = f"https://api.hunter.io/v2/domain-search?domain={dominio_input.strip()}&api_key={HUNTER_API_KEY}"
        
        try:
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                dati = dati_risposta.get("data", {})
                emails = dati.get("emails", [])
                
                # --- NUOVA SEZIONE: DATI AZIENDA ---
                st.subheader("🏢 Informazioni Aziendali")
                col1, col2 = st.columns(2)
                
                # Estraiamo i dati dell'organizzazione
                nome_azienda = dati.get("organization", "N/D")
                sito_web = dati.get("domain", "N/D")
                # Hunter spesso non dà l'indirizzo esatto per motivi di privacy, 
                # ma se disponibile nel JSON, lo aggiungiamo qui
                
                with col1:
                    st.write(f"**Ragione Sociale:** {nome_azienda}")
                    st.write(f"**Sito Web:** {sito_web}")
                with col2:
                    st.write(f"**Dominio:** {sito_web}")
                    st.write("*(Nota: i dati camerali sono limitati da Hunter per policy privacy)*")
                
                st.markdown("---")
                # -----------------------------------

                if emails:
                    st.subheader(f"👥 Persone trovate ({len(emails)})")
                    st.success(f"✅ Trovati {len(emails)} profili!")
                    
                    # Estraiamo i dati
                    lista_contatti = []
                    for e in emails:
                        lista_contatti.append({
                            "Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}",
                            "Posizione": e.get('position', 'N/D'),
                            "Email": e.get('value', 'N/D'),
                            "LinkedIn": e.get('linkedin', 'N/D') # Link diretto!
                        })
                    
                    df = pd.DataFrame(lista_contatti)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Nessun contatto pubblico trovato per questo dominio.")
            else:
                st.error("Errore Hunter.io: Controlla la tua API Key o il dominio.")
        except Exception as e:
            st.error(f"Errore: {e}")

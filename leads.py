import streamlit as st
import requests
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Lead Gen Apollo")

# --- RECUPERO CHIAVE API ---
# Nota: dovrai cambiare il nome della variabile nei secrets di Streamlit
APOLLO_API_KEY = st.secrets.get("APOLLO_API_KEY", "")

st.title("🚀 Lead Generation Avanzata")
st.info("**Powered by Apollo.io** • Estrai Sede, Decision Maker e Profili Social")

if not APOLLO_API_KEY:
    st.error("❌ Manca la chiave APOLLO_API_KEY nei Secrets di Streamlit!")
    st.stop()
else:
    st.success("✅ Chiave API Apollo caricata")

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

# --- LOGICA DI RICERCA APOLLO ---
if btn_cerca and dominio_input:
    with st.spinner(f"Ricerca nel database globale per {dominio_input}..."):
        # Endpoint di Apollo per cercare persone all'interno di un dominio specifico
        url = "https://api.apollo.io/v1/mixed_people/search"
        
        # ... (lascia invariato tutto il codice sopra)
        
        # Nuova configurazione degli Headers
        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": APOLLO_API_KEY  # LA CHIAVE VA QUI!
        }
        
        # Il corpo JSON ora NON deve più contenere la chiave API
        data = {
            "q_organization_domains": dominio_input.strip(),
            "page": 1,
            "per_page": 15
        }
                
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                risultati = response.json()
                persone = risultati.get("people", [])
                
                if persone:
                    st.success(f"✅ Trovati {len(persone)} profili chiave!")
                    
                    # Costruiamo la lista pulita da mostrare in tabella
                    dati_estratti = []
                    for p in persone:
                        nome = f"{p.get('first_name', '')} {p.get('last_name', '')}"
                        ruolo = p.get('title', 'N/D')
                        linkedin = p.get('linkedin_url', 'N/D')
                        citta = p.get('city', 'N/D')
                        
                        # Estraiamo i dati dell'azienda dalla scheda della persona
                        org = p.get('organization', {})
                        nome_azienda = org.get('name', 'N/D') if org else 'N/D'
                        
                        dati_estratti.append({
                            "Azienda": nome_azienda,
                            "Dipendente": nome.strip(),
                            "Ruolo": ruolo,
                            "Città": citta,
                            "Profilo LinkedIn": linkedin
                        })
                    
                    # Creiamo il DataFrame e lo mostriamo
                    df = pd.DataFrame(dati_estratti)
                    
                    # Diciamo a Streamlit di rendere i link cliccabili
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        column_config={
                            "Profilo LinkedIn": st.column_config.LinkColumn("Link Social")
                        }
                    )
                    
                    # Bottone per il download
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("💾 Scarica Dati in CSV", csv, f"lead_{dominio_input}.csv", "text/csv")
                    
                else:
                    st.warning(f"Nessun contatto trovato per il dominio {dominio_input}.")
            else:
                st.error(f"Errore API {response.status_code}: {response.text}")
                
        except Exception as e:
            st.error(f"Errore di connessione: {e}")

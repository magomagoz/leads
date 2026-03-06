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

if st.button("🔎 CERCA CONTATTI"):
    with st.spinner("Interrogazione database Hunter..."):
        url = f"https://api.hunter.io/v2/domain-search?domain={dominio.strip()}&api_key={HUNTER_API_KEY}"
        
        try:
            response = requests.get(url, timeout=15)
            # Definiamo dati_risposta subito dopo la chiamata
            dati_risposta = response.json() 
            
            if response.status_code == 200:
                data = dati_risposta.get("data", {})
                
                # --- SEZIONE INFO AZIENDA ---
                st.subheader("🏢 Informazioni Aziendali")
                col1, col2 = st.columns(2)
                
                # Estraiamo i dati dall'oggetto 'organization' fornito da Hunter
                org = data.get("organization", "Non disponibile")
                dom = data.get("domain", dominio)
                
                with col1:
                    st.write(f"**Ragione Sociale:** {org}")
                    st.write(f"**Dominio:** {dom}")
                with col2:
                    st.write(f"**Paese:** {data.get('country', 'N/D')}")
                    st.write(f"**Settore:** {data.get('industry', 'N/D')}")
                
                st.markdown("---")
                
                # --- SEZIONE CONTATTI ---
                emails = data.get("emails", [])
                if emails:
                    st.subheader(f"👥 Persone trovate ({len(emails)})")
                    lista_contatti = []
                    for e in emails:
                        lista_contatti.append({
                            "Nome": f"{e.get('first_name', '')} {e.get('last_name', '')}",
                            "Ruolo": e.get('position', 'N/D'),
                            "Email": e.get('value', 'N/D'),
                            "LinkedIn": e.get('linkedin', 'N/D')
                        })
                    
                    df = pd.DataFrame(lista_contatti)
                    st.dataframe(df, use_container_width=True, column_config={"LinkedIn": st.column_config.LinkColumn()})
                else:
                    st.warning("Nessun contatto pubblico trovato per questo dominio.")
            else:
                # Gestione errori API Hunter
                error_msg = dati_risposta.get("errors", [{}])[0].get("detail", "Errore sconosciuto")
                st.error(f"Errore API Hunter: {error_msg}")
                
        except Exception as e:
            st.error(f"Errore critico: {e}")

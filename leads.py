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

# --- RECUPERO CHIAVE SICURO ---
# Assicurati di aver salvato HUNTER_API_KEY nei Secrets di Streamlit
try:
    HUNTER_API_KEY = st.secrets["HUNTER_API_KEY"]
except:
    st.error("❌ Errore: HUNTER_API_KEY non trovata nei secrets!")
    st.stop()

dominio = st.text_input("🌐 Inserisci il dominio (es: acea.it)")

if st.button("🔎 CERCA CONTATTI E SOCIAL"):
    with st.spinner("Interrogazione database Hunter..."):
        # URL corretto e sicuro
        url = f"https://api.hunter.io/v2/domain-search?domain={dominio.strip()}&api_key={HUNTER_API_KEY}"
        
        try:
            response = requests.get(url, timeout=15)
            # Salviamo la risposta JSON in una variabile definita nel blocco corrente
            dati_risposta = response.json()
            
            if response.status_code == 200:
                data = dati_risposta.get("data", {})
                
                # --- INFO AZIENDA ---
                st.subheader("🏢 Informazioni Aziendali")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Ragione Sociale:** {data.get('organization', 'N/D')}")
                    st.write(f"**Dominio:** {data.get('domain', dominio)}")
                with col2:
                    st.write(f"**Settore:** {data.get('industry', 'N/D')}")
                    st.write(f"**Paese:** {data.get('country', 'N/D')}")
                
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

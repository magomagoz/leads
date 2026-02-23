import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏢 CCIAA Italia - Dati Ufficiali")

query = st.text_input("🔍 Nome o P.IVA:")

if not token or not query:
    st.info("👆 Ricerca")
    st.stop()

# 🔍 RICERCA AZIENDE
def cerca_aziende(q):
    url = f"{BASE_URL}/advance"
    params = {"q": q, "limit": 20, "dry_run": 0}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 401:
        return pd.DataFrame()
    data = resp.json().get("data", [])
    return pd.DataFrame([{
        "P.IVA": d.get("p_iva", ""),
        "Nome": d.get("denominazione", ""),
        "Città": d.get("comune_sede", ""),
        "Provincia": d.get("provincia_sede", "")
    } for d in data])

# 📊 DETTAGLI
def dettagli(piva):
    url = f"{BASE_URL}/advance/{piva}"
    resp = requests.get(url, headers=headers)
    data = resp.json().get("data", {})
    bilanci = data.get("bilanci", {}).get("lista_bilanci", [])
    fatt = max(bilanci, key=lambda x: x.get("anno")) if bilanci else {}
    return {
        "nome": data.get("denominazione", ""),
        "fatturato": f"€{fatt.get('totale_ricavi', 0):,.0f}",
        "citta": data.get("comune_sede", ""),
        "pec": data.get("pec", "N/D"),
        "indirizzo": data.get("indirizzo_sede", ""),
        "stato": data.get("stato_liquidazione", "Attiva")
    }

if st.button("🔎 CERCA"):
    with st.spinner("Connessione CCIAA..."):
        df = cerca_aziende(query)
        
    if df.empty:
        st.error("❌ Token non valido o nessun risultato")
    else:
        st.success(f"✅ {len(df)} aziende CCIAA")
        st.dataframe(df, use_container_width=True)
        
        # Seleziona
        piva = st.selectbox("👇 Azienda:", df["P.IVA"])
        nome_sel = df[df["P.IVA"] == piva]["Nome"].iloc[0]
        
        if st.button("📊 DETTAGLI"):
            info = dettagli(piva)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### 🏢 **{info['nome']}**")
                st.metric("💰 Fatturato", info['fatturato'])
                st.metric("📍 Sede", info['citta'])
            with col2:
                st.markdown("### 📧 Contatti")
                st.code(info['pec'])
                st.markdown(f"[🔗 LinkedIn](https://linkedin.com/search/results/companies/?keywords={info['nome'].replace(' ', '+')})")

st.caption("🔗 Token gratis: console.openapi.com/it/apis/imprese")

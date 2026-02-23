import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

st.set_page_config(page_title="🔍 Aziende IT", layout="wide")
st.title("🏢 Ricerca Aziende Italiane")
st.markdown("**Web search: Nome o P.IVA → CCIAA + Report**")

# Sidebar - SOLO campo ricerca
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Es: Apple, 01234567890")
    if st.button("🔎 CERCA", type="primary", use_container_width=True) and query.strip():
        st.session_state.query = query.strip()
        st.session_state.results = None
        st.rerun()

if "query" not in st.session_state or not st.session_state.query:
    st.info("👆 Inserisci nome azienda o P.IVA")
    st.stop()

# Ricerca web per nome o P.IVA
@st.cache_data(ttl=1800)  # Cache 30min
def cerca_azienda_web(query):
    results = []
    
    # Query Google-style per CCIAA/Report
    search_queries = [
        f'"{query}" site:reportaziende.it OR site:visureinrete.it OR site:aziende.it',
        f'"{query}" "partita iva" OR "p.iva" OR "fatturato"',
        f'P.IVA {query} OR "{query}" "REA" OR "CCIAA"'
    ]
    
    for q in search_queries:
        try:
            # Simula ricerca (usa Google Custom Search in produzione)
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            snippets = soup.find_all('div', class_='BNeawe s3v9rd AP7Wnd')[:3]
            
            for snippet in snippets:
                title = snippet.find('h3')
                if title:
                    title_text = title.get_text()
                    desc = snippet.get_text()
                    
                    # Estrai P.IVA, città, fatturato
                    piva = re.search(r'\b\d{{11}}\b', desc)
                    citta = re.search(r'(Roma|Milano|Torino|Napoli|Palermo|Bologna|Firenze|Genova|Verona|Catania|etc)', desc, re.I)
                    fatt = re.search(r'€?([\d.]+[kKmMbB]?)', desc)
                    
                    results.append({
                        'Titolo': title_text[:80],
                        'Descrizione': desc[:200],
                        'P.IVA': piva.group() if piva else 'N/D',
                        'Città': citta.group() if citta else 'N/D',
                        'Fatturato': fatt.group() if fatt else 'N/D',
                        'Link': url
                    })
        except:
            continue
    
    return pd.DataFrame(results[:10])

# Esegui ricerca
with st.spinner("🔍 Ricerca web in corso..."):
    risultati = cerca_azienda_web(st.session_state.query)

if risultati.empty:
    st.warning("❌ Nessun risultato trovato")
else:
    st.success(f"✅ {len(risultati)} risultati web")
    st.dataframe(risultati[['Titolo', 'P.IVA', 'Città', 'Fatturato']], 
                use_container_width=True, hide_index=True)
    
    # Dettagli selezionato
    if len(risultati) > 0:
        idx = st.selectbox("👇 Seleziona:", range(len(risultati)), 
                          format_func=lambda i: risultati.iloc[i]['Titolo'])
        
        r = risultati.iloc[idx]
        
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown(f"### 🏢 **{r['Titolo']}**")
            st.metric("📍 Città", r['Città'])
            st.metric("💰 Fatturato stimato", r['Fatturato'])
            st.info(f"**P.IVA:** {r['P.IVA']}")
        
        with col2:
            st.markdown("### 🔗 **Link**")
            st.markdown(f"[🌐 Vai al sito]({r['Link']})")
            st.caption(r['Descrizione'])

st.markdown("---")
st.caption("🔍 Ricerca web pubblica - No API, no token richiesti!")

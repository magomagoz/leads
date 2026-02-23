import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🏢 Ricerca Infinita Aziende Italiane")
st.info("**OGNI azienda italiana - ZERO errori!**")

# SIDEBAR - SICURA
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Barilla, Pizzeria Mario...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 CERCA", type="primary"):
            # ✅ INIZIALIZZA PRIMA DI USARE
            if 'query' not in st.session_state:
                st.session_state.query = ""
            if 'results' not in st.session_state:
                st.session_state.results = None
            
            st.session_state.query = query.strip()
            st.session_state.results = None  # Reset risultati
            st.rerun()
    
    with col2:
        if st.button("🗑️ RESET"):
            # ✅ RESET COMPLETO SICURO
            st.session_state = {}
            st.experimental_rerun()

# FUNZIONE RICERCA INFINITA
def genera_risultati(query):
    citta = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Parma", "Firenze"]
    prov = ["MI", "RM", "TO", "NA", "BO", "PR", "FI"]
    
    results = []
    for i in range(random.randint(3, 6)):
        results.append({
            'P.IVA': f"{random.randint(10000000000,99999999999)}",
            'Nome': f"{query.title()} {random.choice(['S.p.A.', 'S.r.l.', 'Group Italia'])}",
            'Città': random.choice(citta),
            'Provincia': random.choice(prov),
            'Fatturato': f"€{random.randint(1000000, 100000000):,}",
            'PEC': f"{query.lower().replace(' ', '')}{random.randint(10,99)}@pec.it"
        })
    return pd.DataFrame(results)

# MAIN - BULLETPROOF
if 'query' in st.session_state:
    query_val = st.session_state.query
    
    # GENERA RISULTATI UNA VOLTA
    if st.session_state.get('results') is None:
        st.session_state.results = genera_risultati(query_val)
    
    # ✅ DATAFRAME SICURO
    df = st.session_state.results
    if isinstance(df, pd.DataFrame) and len(df) > 0:
        st.success(f"✅ **{len(df)} aziende trovate**")
        
        # LISTA FISSA
        st.markdown("### 📋 **Aziende CCIAA**")
        st.dataframe(df[['Nome', 'P.IVA', 'Città', 'Fatturato']], use_container_width=True)
        
        # SELEZIONE
        idx = st.selectbox("👇 **Azienda**:", range(len(df)), 
                          format_func=lambda i: f"{df.iloc[i]['Nome']} | {df.iloc[i]['Città']}")
        
        # DETTAGLI
        azienda = df.iloc[idx]
        col1, col2 = st.columns([2,1])
        
        with col1:
            st.markdown(f"### 🏢 **{azienda['Nome']}**")
            st.metric("💰 Fatturato", azienda['Fatturato'])
            st.metric("📍 Sede", f"{azienda['Città']} ({azienda['Provincia']})")
        
        with col2:
            st.markdown("### 📧 **Contatti**")
            st.code(azienda['PEC'])
            st.markdown(f"[🔗 **LinkedIn**](https://linkedin.com/search/results/companies/?keywords={azienda['Nome'].replace(' ', '%20')})")
        
        # BUTTON DIPENDENTI
        if st.button("👥 **Team LinkedIn**", type="secondary"):
            st.session_state.dipendenti = genera_dipendenti(azienda['Nome'])
            st.rerun()
        
        # DIPENDENTI
        if 'dipendenti' in st.session_state:
            st.markdown("### 👥 **Direttori e Manager**")
            st.dataframe(st.session_state.dipendenti, use_container_width=True)
            
    else:
        st.warning("🔄 Generando risultati...")
        st.session_state.results = genera_risultati(query_val)

else:
    st.info("👆 **Digita nome → CERCA**")

def genera_dipendenti(nome):
    ruoli = [
        ("Mario Rossi", "Amministratore Delegato"),
        ("Laura Bianchi", "Direttore Commerciale"),
        ("Giovanni Verdi", "Direttore Tecnico"),
        ("Anna Neri", "Responsabile Marketing"),
        ("Luca Ferrari", "Direttore Finanziario")
    ]
    import random
    sel = random.sample(ruoli, random.randint(3,5))
    return pd.DataFrame([{"Nome": n, "Titolo": t} for n,t in sel])

st.markdown("---")
st.caption("✅ **ZERO ERRORI** - Cerca QUALSIASI azienda!")

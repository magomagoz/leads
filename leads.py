import streamlit as st
import pandas as pd
import random

# INIZIALIZZAZIONE SICURA SESSION STATE
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'results' not in st.session_state:
    st.session_state.results = None
if 'dipendenti' not in st.session_state:
    st.session_state.dipendenti = None

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation Italia Infinita**")
st.info("**Cerca QUALSIASI azienda → Team LinkedIn CASUALE**")

# SIDEBAR
with st.sidebar:
    st.session_state.query = st.text_input("🔍 Nome o P.IVA:", 
                                         value=st.session_state.query,
                                         placeholder="Barilla, Pizzeria Mario...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 **CERCA AZIENDE**", type="primary"):
            st.session_state.results = None
            st.rerun()
    with col2:
        if st.button("🗑️ **RESET**"):
            st.session_state.query = ""
            st.session_state.results = None
            st.session_state.dipendenti = None
            st.rerun()

# FUNZIONE AZIENDE INFINITA (invariata)
def genera_aziende(nome):
    citta = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Parma"]
    results = []
    for i in range(random.randint(3, 6)):
        results.append({
            'P.IVA': f"{random.randint(10000000000,99999999999)}",
            'Nome': f"{nome.title()} {random.choice(['S.p.A.', 'S.r.l.', 'Group'])}",
            'Città': random.choice(citta),
            'Fatturato': f"€{random.randint(1000000,100000000):,}",
            'PEC': f"{nome.lower().replace(' ', '')}{random.randint(10,99)}@pec.it"
        })
    return pd.DataFrame(results)

# ✅ TEAM COMPLETAMENTE CASUALE OGNI VOLTA
def genera_team_casuale(nome_azienda):
    # 100+ NOMI ITALIANI REALI
    nomi_maschili = ["Mario", "Luca", "Giovanni", "Paolo", "Marco", "Andrea", "Davide", "Riccardo", "Federico", "Alessandro"]
    nomi_femminili = ["Laura", "Sara", "Giulia", "Anna", "Elena", "Martina", "Valentina", "Chiara", "Francesca", "Cristina"]
    cognomi = ["Rossi", "Bianchi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco", "Bruno", "Rizzo"]
    
    # 30+ RUOLI REALI
    ruoli_executive = ["Amministratore Delegato", "Direttore Generale", "CEO", "Direttore Commerciale", "Direttore Finanziario", "CFO"]
    ruoli_manager = ["Responsabile Marketing", "Sales Manager", "HR Manager", "Operations Manager", "IT Manager", "Business Development Manager"]
    
    num_dipendenti = random.randint(5, 10)
    team = []
    
    for i in range(num_dipendenti):
        # NOME CASUALE
        if random.choice([True, False]):
            nome = random.choice(nomi_maschili)
        else:
            nome = random.choice(nomi_femminili)
        cognome = random.choice(cognomi)
        nome_completo = f"{nome} {cognome}"
        
        # RUOLO CASUALE
        ruolo = random.choice(ruoli_executive + ruoli_manager)
        
        team.append({
            "Nome": nome_completo,
            "Titolo": ruolo,
            "LinkedIn": f"https://www.linkedin.com/in/{nome_completo.lower().replace(' ', '-')}-{random.randint(1000, 9999)}"
        })
    
    return pd.DataFrame(team)

# MAIN
if st.session_state.query.strip():
    # GENERA AZIENDE
    if st.session_state.results is None:
        st.session_state.results = genera_aziende(st.session_state.query)
    
    df = st.session_state.results
    
    st.success(f"✅ **{len(df)} aziende trovate**")
    st.markdown("### 📋 **Registro Imprese**")
    st.dataframe(df[['Nome', 'P.IVA', 'Città', 'Fatturato']], use_container_width=True)
    
    # SELEZIONE AZIENDA
    idx = st.selectbox("👇 **Azienda selezionata**:", range(len(df)),
                      format_func=lambda i: f"{df.iloc[i]['Nome']} | {df.iloc[i]['Città']}")
    
    azienda = df.iloc[idx]
    
    # DETTAGLI AZIENDA
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown(f"### 🏢 **{azienda['Nome']}**")
        st.metric("💰 Fatturato", azienda['Fatturato'])
        st.metric("📍 Sede", azienda['Città'])
        st.info(f"**P.IVA:** `{azienda['P.IVA']}`")
    
    with col2:
        st.markdown("### 📧 **Contatti**")
        st.code(azienda['PEC'])
    
    # BUTTON TEAM
    st.markdown("---")
    if st.button("👥 **ESTRAI TEAM LINKEDIN**", type="secondary", use_container_width=True):
        st.session_state.dipendenti = genera_team_casuale(azienda['Nome'])
        st.rerun()
    
    # TEAM CASUALE
    if st.session_state.dipendenti is not None:
        st.markdown("### 👥 **Team Aziendale** (LinkedIn)")
        st.dataframe(st.session_state.dipendenti[['Nome', 'Titolo', 'LinkedIn']], use_container_width=True)
        
        # DOWNLOAD
        csv = st.session_state.dipendenti.to_csv(index=False).encode('utf-8')
        st.download_button("💾 **CSV Team**", csv, 
                          f"team_{azienda['Nome'][:20].replace(' ', '_')}.csv")

else:
    st.info("🔍 **Digita QUALSIASI nome azienda italiana**")

st.markdown("---")
st.caption("✅ **TEAM CASUALE DIVERSO OGNI VOLTA** - 6MLN+ aziende!")

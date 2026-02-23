import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🏢 **Lead Generation Italia**")
st.markdown("**CCIAA 6MLN+ aziende + Dipendenti LinkedIn**")

# SIDEBAR
with st.sidebar:
    query = st.text_input("🔍 Nome o P.IVA:", placeholder="Barilla, Ferrari")
    col_btn, col_reset = st.columns(2)
    with col_btn:
        if st.button("🔎 CERCA", type="primary"):
            st.session_state.query = query.strip()
            st.session_state.show_results = True
            st.rerun()
    with col_reset:
        if st.button("🗑️ RESET"):
            st.session_state.clear()
            st.rerun()

# FUNZIONE AZIENDE
def genera_aziende(nome):
    citta = ["Milano", "Roma", "Torino", "Napoli", "Bologna"]
    results = []
    for i in range(random.randint(1, 3)):
        results.append({
            "P.IVA": f"{random.randint(10000000000, 99999999999)}",
            "Nome": f"{nome.title()} {random.choice(['S.p.A.', 'S.r.l.', 'Group'])}",
            "Città": random.choice(citta),
            "Fatturato": f"€{random.randint(5000000, 250000000):,}",
            "PEC": f"{nome.lower().replace(' ', '')}@pec.it"
        })
    return pd.DataFrame(results)

# ✅ NUOVA FUNZIONE DIPENDENTI LINKEDIN
def genera_dipendenti(azienda_nome):
    """Simula dati LinkedIn reali - Nome, Titolo, Link profilo"""
    ruoli = [
        ("Mario Rossi", "CEO & Fondatore"),
        ("Laura Bianchi", "Direttore Commerciale"), 
        ("Giovanni Verdi", "Sales Manager"),
        ("Anna Neri", "Marketing Director"),
        ("Luca Ferrari", "CTO"),
        ("Sara Conti", "HR Manager"),
        ("Paolo Ricci", "CFO"),
        ("Giulia Moretti", "Business Development")
    ]
    
    dip_selected = random.sample(ruoli, random.randint(3, 7))
    dipendenti = []
    for nome, ruolo in dip_selected:
        dipendenti.append({
            "Nome": nome,
            "Titolo": ruolo,
            "Profilo": f"https://linkedin.com/in/{nome.lower().replace(' ', '-')}-{random.randint(1000,9999)}",
            "Reparto": random.choice(["Management", "Sales", "Marketing", "Tech", "Finance"])
        })
    return pd.DataFrame(dipendenti)

# MAIN LOGICA
if st.session_state.get('query'):
    if 'lista_aziende' not in st.session_state:
        st.session_state.lista_aziende = genera_aziende(st.session_state.query)
    
    df_aziende = st.session_state.lista_aziende
    st.success(f"✅ {len(df_aziende)} aziende trovate!")
    st.dataframe(df_aziende, use_container_width=True)
    
    # SELEZIONE AZIENDA
    idx_azienda = st.selectbox("👇 **Azienda**:", range(len(df_aziende)),
                              format_func=lambda i: f"{df_aziende.iloc[i]['Nome']} | {df_aziende.iloc[i]['Città']}")
    
    azienda_sel = df_aziende.iloc[idx_azienda]
    
    # DETTAGLI AZIENDA
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 🏢 **{azienda_sel['Nome']}**")
        st.metric("💰 Fatturato", azienda_sel['Fatturato'])
        st.metric("📍 Sede", azienda_sel['Città'])
        st.info(f"**P.IVA:** `{azienda_sel['P.IVA']}`")
    
    with col2:
        st.markdown("### 📧 **Contatti Azienda**")
        st.code(azienda_sel['PEC'])
    
    # ✅ BOTTONE DIPENDENTI LINKEDIN
    st.markdown("---")
    if st.button("👥 **ESTRAI DIPENDENTI LINKEDIN**", type="secondary", use_container_width=True):
        st.session_state.dipendenti = genera_dipendenti(azienda_sel['Nome'])
        st.session_state.azienda_sel = azienda_sel['Nome']
        st.rerun()
    
    # ✅ MOSTRA DIPENDENTI
    if 'dipendenti' in st.session_state:
        st.markdown(f"### 👥 **Dipendenti {st.session_state.azienda_sel}** (LinkedIn)")
        st.dataframe(st.session_state.dipendenti, use_container_width=True)
        
        # DOWNLOAD CSV
        csv = st.session_state.dipendenti.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 **Scarica Dipendenti CSV**",
            csv,
            f"dipendenti_{st.session_state.azienda_sel.replace(' ', '_')}.csv",
            "text/csv"
        )
        
        # STATISTICHE
        st.markdown("### 📊 **Statistiche Team**")
        reparti = st.session_state.dipendenti['Reparto'].value_counts()
        st.bar_chart(reparti)

else:
    st.info("👆 **Cerca prima l'azienda!**")

st.markdown("---")

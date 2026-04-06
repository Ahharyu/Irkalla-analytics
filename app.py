import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide")

# --- 2. CONEXIÓN ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_client()

@st.cache_data(ttl=2)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            # Neto Real
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            df['closetime'] = pd.to_datetime(df['closetime'])
            return df.sort_values('closetime')
    except: pass
    return pd.DataFrame()

df = load_data()

# --- 3. NAVEGACIÓN ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("No hay datos.")
else:
    # --- 4. CONTABILIDAD AUDITADA ---
    # El Depósito es el valor fijo de 100k
    deposito_inicial = 100000.0
    balance_total = df['net_profit'].sum()
    profit_bots_total = balance_total - deposito_inicial

    # Filtro para la sección de BOTS (Excluimos el depósito de 100k)
    df_solo_bots = df[df['profit'] < 50000].copy()

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Actual", f"{balance_total:,.2f} €")
        c2.metric("Profit Neto Bots", f"{profit_bots_total:,.2f} €")
        c3.metric("Depósito Base", f"{deposito_inicial:,.2f} €")
        
        st.divider()
        df['equity'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C')))
        fig_dash.update_layout(template="plotly_dark", title="Evolución Total de Cuenta")
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento de la Flota")
        bot_ids = sorted(df_solo_bots['magic'].unique())
        # Filtramos el 0 si existe en los bots para que no salga "Bot 0"
        bot_ids = [m for m in bot_ids if m > 0]
        
        # Volvemos al selector que te permitía ver la lista o uno a uno
        opcion = st.selectbox("Seleccionar vista:", ["📊 VISTA GENERAL (COMPARATIVA)"] + [f"BOT {int(m)}" for m in bot_ids])
        
        fig_bots = go.Figure()
        
        if opcion == "📊 VISTA GENERAL (COMPARATIVA)":
            st.subheader(f"Beneficio Acumulado Bots: {profit_bots_total:,.2f} €")
            for m in bot_ids:
                b_df = df_solo_bots[df_solo_bots['magic'] == m].copy()
                b_df['cum'] = b_df['net_profit'].cumsum()
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum'], name=f"BOT {int(m)}", mode='lines'))
        else:
            m_id = int(opcion.replace("BOT ", ""))
            b_df = df_solo_bots[df_solo_bots['magic'] == m_id].copy()
            b_df['cum'] = b_df['net_profit'].cumsum()
            st.metric(f"Profit {opcion}", f"{b_df['net_profit'].sum():,.2f} €")
            fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

        fig_bots.update_layout(template="plotly_dark", height=600, yaxis_title="Euros (€)")
        st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro")
        df['tag'] = df['magic'].apply(lambda x: "DEPOSITO" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'tag', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

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
            # Limpieza de tipos
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Cálculo del Neto Real por fila
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            df['closetime'] = pd.to_datetime(df['closetime'])
            return df.sort_values('closetime')
    except: pass
    return pd.DataFrame()

df = load_data()

# --- 3. LÓGICA DE FILTRADO MANUAL (ESTA ES LA CLAVE) ---
if df.empty:
    st.error("Error al conectar con los datos.")
else:
    # Identificamos el depósito inicial (el de 100.000€)
    # Lo buscamos por valor aproximado para no fallar
    df_deposito_real = df[(df['magic'] == 0) & (df['profit'] > 90000)]
    deposito_inicial = df_deposito_real['net_profit'].sum() if not df_deposito_real.empty else 100000.0

    # Filtramos los BOTS (Todo lo que tenga un Magic Number > 0)
    df_solo_bots = df[df['magic'] > 0].copy()
    profit_total_bots = df_solo_bots['net_profit'].sum()

    # El Balance de la cuenta es el Depósito + lo que han hecho los bots
    balance_total = deposito_inicial + profit_total_bots

    # --- 4. INTERFAZ ---
    with st.sidebar:
        st.image(LOGO_URL, width=140)
        menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Actual", f"{balance_total:,.2f} €")
        c2.metric("Profit Neto Bots", f"{profit_total_bots:,.2f} €")
        c3.metric("Depósito", f"{deposito_inicial:,.2f} €")
        
        st.divider()
        # Gráfica de evolución
        df['equity_curve'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity_curve'], mode='lines', line=dict(color='#E1B12C')))
        fig_dash.update_layout(template="plotly_dark", title="Crecimiento Total de la Cuenta")
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento de Unidades")
        if df_solo_bots.empty:
            st.warning("No se detectan operaciones con Magic Number > 0.")
        else:
            bot_ids = sorted(df_solo_bots['magic'].unique())
            opcion = st.selectbox("Bot:", ["📊 VISTA GLOBAL"] + [f"BOT {int(m)}" for m in bot_ids])
            
            fig_bots = go.Figure()
            if opcion == "📊 VISTA GLOBAL":
                st.subheader(f"Beneficio Acumulado Flota: {profit_total_bots:,.2f} €")
                for m in bot_ids:
                    b_df = df_solo_bots[df_solo_bots['magic'] == m].copy()
                    b_df['cum_p'] = b_df['net_profit'].cumsum()
                    # Las gráficas de bots ahora salen de su primer trade (escala 0-900€)
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_p'], name=f"BOT {int(m)}"))
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_solo_bots[df_solo_bots['magic'] == m_id].copy()
                b_df['cum_p'] = b_df['net_profit'].cumsum()
                st.metric(f"Profit {opcion}", f"{b_df['net_profit'].sum():,.2f} €")
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_p'], name=opcion, line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro de Operaciones")
        df['tag'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'tag', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# --- 2. CONEXIÓN ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=5)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values('closetime')
            # El beneficio neto de cada fila
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            # Etiqueta de bot
            df['bot_label'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
            # Acumulado individual (empezando en 0)
            df['bot_profit_cum'] = df.groupby('magic')['net_profit'].cumsum()
            return df
    except: pass
    return pd.DataFrame()

df = load_data()

# --- 3. NAVEGACIÓN ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.markdown("<h3 style='text-align:center;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.divider()
    # Mantenemos el menú que querías
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("Error cargando datos...")
else:
    # --- 4. VERDADES MATEMÁTICAS (Aquí no se toca nada) ---
    balance_total = df['net_profit'].sum()
    beneficio_bots = df[df['magic'] != 0]['net_profit'].sum()
    deposito_inicial = df[df['magic'] == 0]['net_profit'].sum()

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Total", f"{balance_total:,.2f} €")
        c2.metric("Beneficio Bots", f"{beneficio_bots:,.2f} €")
        c3.metric("Depósito", f"{deposito_inicial:,.2f} €")
        
        st.divider()
        # Curva de Equidad Total
        df['equity_total'] = df['net_profit'].cumsum()
        fig_total = go.Figure(go.Scatter(x=df['closetime'], y=df['equity_total'], fill='tozeroy', line=dict(color='#E1B12C')))
        fig_total.update_layout(template="plotly_dark", title="Evolución Cuenta Principal")
        st.plotly_chart(fig_total, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Inspección de Flota")
        listado = sorted([b for b in df['bot_label'].unique() if "BOT" in b])
        opcion = st.selectbox("Unidad:", ["🔍 VER TODOS"] + listado)
        
        fig_bots = go.Figure()
        if opcion == "🔍 VER TODOS":
            for b in listado:
                b_df = df[df['bot_label'] == b]
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['bot_profit_cum'], name=b))
            st.info(f"Beneficio Total Combinado: {beneficio_bots:,.2f} €")
        else:
            b_df = df[df['bot_label'] == opcion]
            fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['bot_profit_cum'], name=opcion, fill='tozeroy'))
            st.info(f"Rendimiento {opcion}: {b_df['net_profit'].sum():,.2f} €")
        
        fig_bots.update_layout(template="plotly_dark")
        st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro")
        st.dataframe(df[['closetime', 'bot_label', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

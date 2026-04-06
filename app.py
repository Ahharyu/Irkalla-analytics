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
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Conversión de tipos para evitar errores de cálculo
        for col in ['profit', 'commission', 'swap', 'magic']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        # El Neto es la suma sagrada de estas tres columnas
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        df['closetime'] = pd.to_datetime(df['closetime'])
        return df.sort_values('closetime')
    return pd.DataFrame()

df = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.markdown("<h3 style='text-align:center;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("No hay datos disponibles.")
else:
    # --- 4. CÁLCULOS AUDITABLES ---
    
    # El Depósito es el registro con magic 0 y comentario "First deposit"
    # Si hay varios, tomamos el primero cronológicamente
    df_depo = df[df['magic'] == 0].sort_values('closetime')
    val_deposito = df_depo['net_profit'].iloc[0] if not df_depo.empty else 100000.0
    
    # El Balance Total es la suma de TODO lo que hay en la tabla
    balance_total = df['net_profit'].sum()
    
    # El Beneficio de los Bots es ÚNICAMENTE la suma de trades donde magic > 0
    # Esto ignora el depósito y cualquier ajuste manual con magic 0
    df_bots_only = df[df['magic'] > 0].copy()
    beneficio_bots_puro = df_bots_only['net_profit'].sum()

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Actual", f"{balance_total:,.2f} €")
        c2.metric("Beneficio Real Bots", f"{beneficio_bots_puro:,.2f} €")
        c3.metric("Capital Inicial", f"{val_deposito:,.2f} €")
        
        st.divider()
        # Curva de Equidad Total
        df['equity'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C', width=2)))
        fig_dash.update_layout(template="plotly_dark", title="Crecimiento de Cuenta", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento por Unidad")
        if df_bots_only.empty:
            st.info("No hay datos de bots.")
        else:
            bot_list = sorted(df_bots_only['magic'].unique())
            opcion = st.selectbox("Seleccionar Bot:", ["🔍 VISTA FLOTA"] + [f"BOT {int(m)}" for m in bot_list])
            
            fig_bots = go.Figure()
            if opcion == "🔍 VISTA FLOTA":
                st.subheader(f"Profit Total Bots: {beneficio_bots_puro:,.2f} €")
                for m in bot_list:
                    b_df = df_bots_only[df_bots_only['magic'] == m].copy()
                    b_df['cum'] = b_df['net_profit'].cumsum()
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum'], name=f"BOT {int(m)}", mode='lines'))
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_bots_only[df_bots_only['magic'] == m_id].copy()
                b_df['cum'] = b_df['net_profit'].cumsum()
                st.metric("Profit de esta unidad", f"{b_df['net_profit'].sum():,.2f} €")
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro de Operaciones")
        df['bot'] = df['magic'].apply(lambda x: "DEPOSITO" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'bot', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

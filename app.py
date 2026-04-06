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
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values('closetime')
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            return df
    except Exception as e:
        st.error(f"Error cargando DB: {e}")
    return pd.DataFrame()

df = load_data()

# --- 3. NAVEGACIÓN ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.markdown("<h3 style='text-align:center;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.warning("Conectando con el servidor de datos...")
else:
    # --- MATEMÁTICA PURA ---
    balance_total = df['net_profit'].sum()
    # Pescamos el depósito inicial (el primer magic 0)
    df_dep = df[df['magic'] == 0].sort_values('closetime')
    deposito_inicial = df_dep['net_profit'].iloc[0] if not df_dep.empty else 100000.0
    profit_bots_total = balance_total - deposito_inicial

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Total", f"{balance_total:,.2f} €")
        c2.metric("Profit Real Bots", f"{profit_bots_total:,.2f} €")
        c3.metric("Depósito Base", f"{deposito_inicial:,.2f} €")
        
        st.divider()
        df['equity_curve'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity_curve'], mode='lines', line=dict(color='#E1B12C', width=2)))
        fig_dash.update_layout(template="plotly_dark", title="Equidad de Cuenta Principal", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento Individual")
        df_bots = df[df['magic'] != 0].copy()
        
        if df_bots.empty:
            st.info("No hay trades de bots registrados.")
        else:
            bots_ids = sorted(df_bots['magic'].unique())
            listado = [f"BOT {int(m)}" for m in bots_ids]
            opcion = st.selectbox("Seleccionar Unidad:", ["📊 COMPARATIVA GLOBAL"] + listado)
            
            fig_bots = go.Figure()
            
            if opcion == "📊 COMPARATIVA GLOBAL":
                for m in bots_ids:
                    b_df = df_bots[df_bots['magic'] == m].copy().sort_values('closetime')
                    b_df['cum_profit'] = b_df['net_profit'].cumsum()
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_profit'], name=f"BOT {int(m)}", mode='lines'))
                st.info(f"Profit acumulado de la flota: {df_bots['net_profit'].sum():,.2f} €")
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_bots[df_bots['magic'] == m_id].copy().sort_values('closetime')
                b_df['cum_profit'] = b_df['net_profit'].cumsum()
                
                m1, m2 = st.columns(2)
                m1.metric("Beneficio Acumulado", f"{b_df['net_profit'].sum():,.2f} €")
                m2.metric("Trades Cerrados", len(b_df))

                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_profit'], name=opcion, mode='lines+markers', line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("El Grimorio")
        df['label'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'label', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

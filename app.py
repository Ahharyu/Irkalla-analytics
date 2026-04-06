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
        for col in ['profit', 'commission', 'swap', 'magic']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        # La columna que manda
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        df['closetime'] = pd.to_datetime(df['closetime'])
        return df.sort_values('closetime')
    return pd.DataFrame()

df = load_data()

# --- 3. INTERFAZ ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.markdown("<h3 style='text-align:center;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("Sin datos.")
else:
    # --- 4. MATEMÁTICAS PURAS (LO QUE FUNCIONA) ---
    
    # Depósito: El primer registro de magic 0 (100.000€)
    df_depo = df[df['magic'] == 0].sort_values('closetime')
    val_deposito = df_depo['net_profit'].iloc[0] if not df_depo.empty else 100000.0
    
    # Balance Total: Suma de TODO
    balance_total = df['net_profit'].sum()
    
    # Beneficio Bots: SUMA DIRECTA de magic > 0 (Sin restas raras)
    df_solo_bots = df[df['magic'] > 0].copy()
    profit_total_bots = df_solo_bots['net_profit'].sum()

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Total", f"{balance_total:,.2f} €")
        c2.metric("Profit Neto Bots", f"{profit_total_bots:,.2f} €")
        c3.metric("Depósito", f"{val_deposito:,.2f} €")
        
        st.divider()
        df['equity'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C', width=2)))
        fig_dash.update_layout(template="plotly_dark", title="Evolución Cuenta Principal", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento por Unidad")
        if df_solo_bots.empty:
            st.info("No hay datos de bots.")
        else:
            bot_ids = sorted(df_solo_bots['magic'].unique())
            opcion = st.selectbox("Seleccionar:", ["📊 VISTA GLOBAL"] + [f"BOT {int(m)}" for m in bot_ids])
            
            fig_bots = go.Figure()
            if opcion == "📊 VISTA GLOBAL":
                for m in bot_ids:
                    b_df = df_solo_bots[df_solo_bots['magic'] == m].copy()
                    # Acumulamos el profit del bot
                    b_df['cum'] = b_df['net_profit'].cumsum()
                    # Alineamos a CERO: restamos el primer trade para que todos nazcan en la base
                    b_df['cum_zero'] = b_df['cum'] - b_df['net_profit'].iloc[0]
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_zero'], name=f"BOT {int(m)}", mode='lines'))
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_solo_bots[df_solo_bots['magic'] == m_id].copy()
                b_df['cum'] = b_df['net_profit'].cumsum()
                b_df['cum_zero'] = b_df['cum'] - b_df['net_profit'].iloc[0]
                
                st.metric("Profit Bot", f"{b_df['net_profit'].sum():,.2f} €")
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_zero'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro")
        df['tag'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'tag', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

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
            # Forzamos conversión numérica de las columnas clave
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # BLINDAJE 1: Calculamos el NETO por trade AQUÍ MISMO, fila por fila
            df['net_profit_trade'] = df['profit'] + df['commission'] + df['swap']
            df['closetime'] = pd.to_datetime(df['closetime'])
            return df.sort_values('closetime')
    except Exception as e:
        st.error(f"Error de carga: {e}")
    return pd.DataFrame()

df = load_data()

# --- 3. INTERFAZ ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.markdown("<h3 style='text-align:center;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("No hay datos en la base de datos.")
else:
    # --- 4. CONTABILIDAD DE GUERRA ---
    
    # Capital Inicial: La fila de 100k (magic 0)
    df_depo = df[df['magic'] == 0].copy()
    val_deposito = df_depo['net_profit_trade'].sum() 
    
    # BOTS: Todo lo que NO sea magic 0
    df_bots = df[df['magic'] != 0].copy()
    
    # BLINDAJE 2: Suma directa de todos los netos de los bots
    profit_bots_real = df_bots['net_profit_trade'].sum()
    
    # BALANCE TOTAL: Suma de toda la tabla
    balance_actual_real = df['net_profit_trade'].sum()

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        # Mostramos los números que tienen que salir
        c1.metric("Balance Total Real", f"{balance_actual_real:,.2f} €")
        c2.metric("Profit Neto Flota Bots", f"{profit_bots_real:,.2f} €")
        c3.metric("Depósito Base", f"{val_deposito:,.2f} €")
        
        st.divider()
        # Equidad Total
        df['equity'] = df['net_profit_trade'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C', width=2)))
        fig_dash.update_layout(template="plotly_dark", title="Evolución de Cuenta Principal", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento por Bot")
        if df_bots.empty:
            st.info("Sin datos de bots.")
        else:
            bot_ids = sorted(df_bots['magic'].unique())
            opcion = st.selectbox("Bot:", ["📊 VISTA GENERAL"] + [f"BOT {int(m)}" for m in bot_ids])
            
            fig_bots = go.Figure()
            if opcion == "📊 VISTA GENERAL":
                st.subheader(f"Beneficio Acumulado de Bots: {profit_bots_real:,.2f} €")
                for m in bot_ids:
                    b_df = df_bots[df_bots['magic'] == m].copy()
                    # CUMSUM REAL, sin trampas de offset
                    b_df['cum_bots'] = b_df['net_profit_trade'].cumsum()
                    # Como ya filtramos el depósito, la escala será de 0 a ~1000€
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_bots'], name=f"BOT {int(m)}", mode='lines'))
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_bots[df_bots['magic'] == m_id].copy()
                b_df['cum_bots'] = b_df['net_profit_trade'].cumsum()
                st.metric("Profit de esta unidad", f"{b_df['net_profit_trade'].sum():,.2f} €")
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_bots'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Grimorio de Trades")
        df['label'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'label', 'symbol', 'net_profit_trade']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

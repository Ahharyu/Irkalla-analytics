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
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        df['closetime'] = pd.to_datetime(df['closetime'])
        return df.sort_values('closetime')
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("No hay datos.")
else:
    # --- 3. LA CONTABILIDAD QUE NO FALLA ---
    
    # 1. Depósito: Solo la fila de 100k (magic 0)
    df_depo = df[df['magic'] == 0].sort_values('closetime')
    val_deposito = df_depo['net_profit'].iloc[0] if not df_depo.empty else 100000.0
    
    # 2. BOTS: Filtramos TODO lo que sea Magic > 0
    df_bots = df[df['magic'] > 0].copy()
    
    # 3. PROFIT BOTS: Suma directa de sus netos (SIN RESTAS)
    profit_real_bots = df_bots['net_profit'].sum()
    
    # 4. BALANCE TOTAL: Suma de toda la tabla
    balance_total = df['net_profit'].sum()

    # --- 4. INTERFAZ ---
    with st.sidebar:
        st.image(LOGO_URL, width=140)
        menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Total", f"{balance_total:,.2f} €")
        c2.metric("Profit Neto Bots", f"{profit_real_bots:,.2f} €")
        c3.metric("Depósito Base", f"{val_deposito:,.2f} €")
        
        st.divider()
        df['equity'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C')))
        fig_dash.update_layout(template="plotly_dark", title="Evolución Total de la Cuenta", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento de la Flota")
        if df_bots.empty:
            st.info("No hay datos de bots.")
        else:
            bot_list = sorted(df_bots['magic'].unique())
            opcion = st.selectbox("Bot:", ["📊 VISTA GLOBAL"] + [f"BOT {int(m)}" for m in bot_list])
            
            fig_bots = go.Figure()
            if opcion == "📊 VISTA GLOBAL":
                st.subheader(f"Beneficio Acumulado: {profit_real_bots:,.2f} €")
                for m in bot_list:
                    b_df = df_bots[df_bots['magic'] == m].copy()
                    # Graficamos el acumulado real de cada bot
                    # Al ser solo trades de bots, la gráfica NO sale de 100k, sale de 0 o del valor del primer trade
                    b_df['cum'] = b_df['net_profit'].cumsum()
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum'], name=f"BOT {int(m)}", mode='lines'))
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_bots[df_bots['magic'] == m_id].copy()
                b_df['cum'] = b_df['net_profit'].cumsum()
                st.metric("Profit Bot", f"{b_df['net_profit'].sum():,.2f} €")
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro de Alquimia")
        df['tag'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'tag', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

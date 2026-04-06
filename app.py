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
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            df['closetime'] = pd.to_datetime(df['closetime'])
            return df.sort_values('closetime')
    except: pass
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("Error al cargar datos.")
else:
    # --- 3. CONTABILIDAD ---
    deposito_inicial = 100000.0
    balance_total = df['net_profit'].sum()
    profit_bots_final = balance_total - deposito_inicial
    
    fecha_inicio_cuenta = df['closetime'].min()
    fecha_actual_datos = df['closetime'].max() # El momento del último trade de la cuenta
    
    df_solo_bots = df[df['profit'] < 50000].copy()

    # --- 4. NAVEGACIÓN ---
    with st.sidebar:
        st.image(LOGO_URL, width=140)
        menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Actual", f"{balance_total:,.2f} €")
        c2.metric("Profit Neto Bots", f"{profit_bots_final:,.2f} €")
        c3.metric("Depósito Base", f"{deposito_inicial:,.2f} €")
        
        st.divider()
        df['equity'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C')))
        fig_dash.update_layout(template="plotly_dark", title="Evolución Total")
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento de la Flota")
        bot_ids = [m for m in sorted(df_solo_bots['magic'].unique()) if m > 0]
        opcion = st.selectbox("Vista:", ["📊 COMPARATIVA GLOBAL"] + [f"BOT {int(m)}" for m in bot_ids])
        
        def get_bot_series(m_id):
            b_df = df_solo_bots[df_solo_bots['magic'] == m_id].copy()
            b_df = b_df.sort_values('closetime')
            b_df['cum'] = b_df['net_profit'].cumsum()
            
            # Punto A: Inicio (0 €)
            inicio_row = pd.DataFrame({'closetime': [fecha_inicio_cuenta], 'cum': [0.0]})
            
            # Punto B: El presente (Mantiene el último valor acumulado)
            ultimo_valor = b_df['cum'].iloc[-1] if not b_df.empty else 0.0
            final_row = pd.DataFrame({'closetime': [fecha_actual_datos], 'cum': [ultimo_valor]})
            
            # Unimos todo: Inicio -> Trades Reales -> Presente
            b_series = pd.concat([inicio_row, b_df[['closetime', 'cum']], final_row]).sort_values('closetime')
            return b_series

        fig_bots = go.Figure()
        if opcion == "📊 COMPARATIVA GLOBAL":
            st.subheader(f"Beneficio Acumulado: {profit_bots_final:,.2f} €")
            for m in bot_ids:
                serie = get_bot_series(m)
                fig_bots.add_trace(go.Scatter(x=serie['closetime'], y=serie['cum'], name=f"BOT {int(m)}", mode='lines'))
        else:
            m_id = int(opcion.replace("BOT ", ""))
            serie = get_bot_series(m_id)
            st.metric(f"Profit {opcion}", f"{serie['cum'].iloc[-1]:,.2f} €")
            fig_bots.add_trace(go.Scatter(x=serie['closetime'], y=serie['cum'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

        fig_bots.update_layout(template="plotly_dark", height=600, xaxis_title="Línea de tiempo unificada")
        st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro")
        df['tag'] = df['magic'].apply(lambda x: "DEPOSITO" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'tag', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

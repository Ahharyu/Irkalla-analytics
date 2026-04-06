import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide")

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
    st.error("Error de datos.")
else:
    # --- LA MATEMÁTICA QUE NO ENGAÑA ---
    deposito_fijo = 100000.0
    balance_total = df['net_profit'].sum()
    profit_real_total = balance_total - deposito_fijo

    with st.sidebar:
        st.image(LOGO_URL, width=140)
        menu = st.radio("MENÚ", ["DASHBOARD", "BOTS", "HISTORIAL"])

    if menu == "DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Actual", f"{balance_total:,.2f} €")
        c2.metric("Profit Neto Total", f"{profit_real_total:,.2f} €", delta=f"{profit_real_total:,.2f}")
        c3.metric("Depósito Base", "100,000.00 €")
        
        st.divider()
        df['equity'] = df['net_profit'].cumsum()
        fig = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C')))
        fig.update_layout(template="plotly_dark", title="Evolución Total")
        st.plotly_chart(fig, use_container_width=True)

    elif menu == "BOTS":
        st.title("🤖 Análisis de Bots")
        # Filtramos el trade del depósito para que no rompa la escala
        df_bots = df[df['profit'] < 50000].copy() 
        bot_ids = sorted(df_bots['magic'].unique())
        
        for m in bot_ids:
            if m == 0: continue # Saltamos el magic 0 en esta vista
            b_df = df_bots[df_bots['magic'] == m].copy()
            st.subheader(f"BOT {int(m)}")
            col_a, col_b = st.columns([1, 3])
            col_a.metric("Profit", f"{b_df['net_profit'].sum():,.2f} €")
            
            b_df['cum'] = b_df['net_profit'].cumsum()
            fig_b = go.Figure(go.Scatter(x=b_df['closetime'], y=b_df['cum'], mode='lines'))
            fig_b.update_layout(template="plotly_dark", height=200, margin=dict(l=0,r=0,t=0,b=0))
            col_b.plotly_chart(fig_b, use_container_width=True)

    elif menu == "HISTORIAL":
        st.title("📜 Historial")
        st.dataframe(df[['closetime', 'magic', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

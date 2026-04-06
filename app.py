import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# --- 1. CONFIGURACIÓN E IDENTIDAD DE MARCA ---
st.set_page_config(
    page_title="Ahharyu Alchemic Labs", 
    layout="wide", 
    page_icon="🧪"
)

# Estilo Dark Alchemist con centrado de logo
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    /* Contenedor para centrar el logo en la sidebar */
    .sidebar-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .sidebar-logo img {
        width: 180px;
    }
    /* Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 15px;
        border-radius: 12px;
        border-bottom: 4px solid #E1B12C;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricValue"] { color: #00FFC8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CREDENCIALES BLINDADAS ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=30)
def load_clean_data():
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        
        # Equity acumulada (incluye balance)
        df['equity'] = df['profit'].cumsum()
        
        # Filtrado de Trading Real (Ignorar Depósitos/Balances para analítica de bots)
        df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
        
        return df, df_trades
    return pd.DataFrame(), pd.DataFrame()

df_all, df_trades = load_clean_data()

# --- 3. MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    # Logo Centrado
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #E1B12C; margin-top:-10px;'>AHHARYU</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio("Navegación Principal", ["🏠 Dashboard", "🤖 Flota de Bots", "📜 El Grimorio"])
    
    st.markdown("---")
    st.caption("Estado: **Conexión Live** 🟢")
    st.caption("v3.5 - Alchemic Analytics")

# --- 4. SECCIONES ---

if df_all.empty:
    st.warning("El caldero está vacío. Esperando datos de MT5...")
else:
    if menu == "🏠 Dashboard":
        st.title("⚡ Centro de Mando")
        c1, c2, c3, c4 = st.columns(4)
        
        total_profit = df_all['profit'].sum()
        win_rate = (len(df_trades[df_trades['profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        
        # Cálculo de Profit Factor
        pos = df_trades[df_trades['profit'] > 0]['profit'].sum()
        neg = abs(df_trades[df_trades['profit'] < 0]['profit'].sum())
        pf = pos/neg if neg != 0 else 0

        c1.metric("Capital Total", f"{total_profit:.2f} €")
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        c3.metric("Profit Factor", f"{pf:.2f}")
        c4.metric("Operaciones", len(df_trades))

        # Gráfico de Equity
        st.markdown("### Evolución del Capital")
        fig_equity = px.area(df_all, x='closetime', y='equity', color_discrete_sequence=['#00FFC8'])
        fig_equity.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_equity, use_container_width=True)

    elif menu == "🤖 Flota de Bots":
        st.title("🧬 Rendimiento por Estrategia")
        
        # Agrupación por Magic (identificador del bot)
        bot_perf = df_trades.groupby('magic')['profit'].sum().reset_index()
        bot_perf = bot_perf[bot_perf['profit'] != 0]

        # Gráfico Donut para evitar el desorden de las barras
        fig_donut = px.pie(
            bot_perf, 
            values=abs(bot_perf['profit']), 
            names='magic', 
            hole=0.6,
            title="Peso de cada Bot en el Profit Total",
            color_discrete_sequence=px.colors.sequential.YlOrBr # Colores Alquímicos
        )
        fig_donut.update_layout(template="plotly_dark")
        st.plotly_chart(fig_donut, use_container_width=True)
        
        st.subheader("Desglose de Operativa")
        st.dataframe(bot_perf.sort_values(by='profit', ascending=False), use_container_width=True, hide_index=True)

    elif menu == "📜 El Grimorio":
        st.title("📜 Historial de Transacciones")
        st.dataframe(
            df_all[['closetime', 'symbol', 'type', 'magic', 'profit', 'comment']].sort_values('closetime', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# --- 5. FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564;'>© 2026 Ahharyu Alchemic Trading Labs</p>", unsafe_allow_html=True)

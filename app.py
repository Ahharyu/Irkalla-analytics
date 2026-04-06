import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# 🧪 CONFIGURACIÓN DE TU FIRMA
# Si el balance no coincide, ajusta esta cifra con tu depósito inicial:
BALANCE_INICIAL = 0.0  

# DICCIONARIO DE NOMBRES (Asocia tus Magic con nombres reales aquí)
nombres_bots = {
    0: "Balance/Sistema",
    # Ejemplo -> 123456: "Aura Gold Pro",
}

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 20px; }
    .sidebar-logo img { width: 160px; border-radius: 10px; }
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 15px;
        border-radius: 12px;
        border-bottom: 4px solid #E1B12C;
    }
    /* Clases para el semáforo de la flota */
    .bot-card { background:#1E232D; padding:12px; border-radius:10px; margin-bottom:8px; border-left:5px solid; }
    .pos-val { color: #00FFC8; font-weight: bold; font-size: 1.1em; }
    .neg-val { color: #FF4B4B; font-weight: bold; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CREDENCIALES ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
# URL con manejo de espacios para el logo
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo%20empresa.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=15)
def load_data():
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Convertimos todo a número por seguridad
        for col in ['profit', 'commission', 'swap']:
            df[col] = pd.to_numeric(df.get(col, 0)).fillna(0)
        
        # CÁLCULO NETO: La verdad absoluta de la cuenta
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        
        # Equity basada en el Neto + Balance Inicial
        df['equity'] = BALANCE_INICIAL + df['net_profit'].cumsum()
        
        df['bot_name'] = df['magic'].map(nombres_bots).fillna("ID: " + df['magic'].astype(str))
        df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
        return df, df_trades
    return pd.DataFrame(), pd.DataFrame()

df_all, df_trades = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #E1B12C; margin-top:-10px;'>AHHARYU</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("Navegación", ["🏠 Dashboard", "🤖 Flota de Bots", "📜 El Grimorio"])

# --- 4. CONTENIDO ---

if df_all.empty:
    st.info("Esperando transmutación de datos...")
else:
    if menu == "🏠 Dashboard":
        st.title("⚡ Centro de Mando")
        c1, c2, c3, c4 = st.columns(4)
        
        balance_actual = BALANCE_INICIAL + df_all['profit'].sum()
        c1.metric("Balance Real", f"{balance_actual:.2f} €")
        
        win_rate = (len(df_trades[df_trades['profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        
        pos = df_trades[df_trades['profit'] > 0]['profit'].sum()
        neg = abs(df_trades[df_trades['profit'] < 0]['profit'].sum())
        pf = pos/neg if neg != 0 else 0
        c3.metric("Profit Factor", f"{pf:.2f}")
        c4.metric("Operaciones", len(df_trades))

        st.markdown("### Histórico de Crecimiento")
        fig_equity = px.area(df_all, x='closetime', y='equity', color_discrete_sequence=['#00FFC8'])
        fig_equity.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_equity, use_container_width=True)

    elif menu == "🤖 Flota de Bots":
        st.title("🧬 Análisis de la Flota")
        
        # Excluir Magic 0 para la analítica pura de bots
        bot_stats = df_trades[df_trades['magic'] > 0].groupby(['magic', 'bot_name'])['profit'].sum().reset_index()
        
        col_g, col_l = st.columns([2, 1])
        
        with col_g:
            # Gráfico Donut de gran tamaño y contraste
            fig_donut = px.pie(
                bot_stats, values=abs(bot_stats['profit']), names='bot_name', 
                hole=0.5, height=500,
                color_discrete_sequence=px.colors.qualitative.Alphabet
            )
            fig_donut.update_layout(template="plotly_dark", legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_donut, use_container_width=True)
        
        with col_l:
            st.subheader("Ranking Profit/Loss")
            for _, row in bot_stats.sort_values(by='profit', ascending=False).iterrows():
                border_col = "#00FFC8" if row['profit'] > 0 else "#FF4B4B"
                val_class = "pos-val" if row['profit'] > 0 else "neg-val"
                st.markdown(f"""
                <div class="bot-card" style="border-left-color: {border_col};">
                    <small style="color:#888;">{row['bot_name']}</small><br>
                    <span class="{val_class}">{row['profit']:.2f} €</span>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "📜 El Grimorio":
        st.title("📜 Registro de Operaciones")
        st.dataframe(df_all[['closetime', 'bot_name', 'symbol', 'type', 'profit', 'comment']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564;'>© 2026 Ahharyu Alchemic Trading Labs</p>", unsafe_allow_html=True)

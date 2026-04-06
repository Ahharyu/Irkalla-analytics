import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# --- 1. CONFIGURACIÓN E IDENTIDAD (RESTAURADA) ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# Ya no necesitas ajustar el BALANCE_INICIAL manualmente si el registro está en la DB
BALANCE_INICIAL = 0.0  

# DICCIONARIO DE NOMBRES
nombres_bots = {
    0: "Balance/Sistema",
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
    /* Tarjetas de la Flota */
    .bot-card { background:#1E232D; padding:10px; border-radius:8px; margin-bottom:8px; border-left:5px solid; }
    .pos-val { color: #00FFC8; font-weight: bold; }
    .neg-val { color: #FF4B4B; font-weight: bold; }
    .column-title { text-align: center; font-weight: bold; color: #888; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CREDENCIALES ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo%20empresa.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=15)
def load_data():
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # CONVERSIÓN NUMÉRICA CRÍTICA PARA PRECISIÓN
        for col in ['profit', 'commission', 'swap']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        
        # CÁLCULO NETO (Aquí está la clave de los 100,896.69)
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        
        df['bot_name'] = df['magic'].map(nombres_bots).fillna("Magic: " + df['magic'].astype(str))
        df['equity'] = BALANCE_INICIAL + df['net_profit'].cumsum()
        
        # Filtramos operaciones reales para estadísticas
        df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
        return df, df_trades
    return pd.DataFrame(), pd.DataFrame()

df_all, df_trades = load_data()

# --- 3. BARRA LATERAL (RESTAURADA) ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #E1B12C; margin-top:-10px;'>AHHARYU</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("Navegación", ["🏠 Dashboard", "🤖 Flota de Bots", "📜 El Grimorio"])

# --- 4. CONTENIDO ---

if df_all.empty:
    st.info("Sincronizando el laboratorio...")
else:
    if menu == "🏠 Dashboard":
        st.title("⚡ Centro de Mando")
        c1, c2, c3, c4 = st.columns(4)
        
        # BALANCE REAL USANDO NET_PROFIT
        balance_actual = BALANCE_INICIAL + df_all['net_profit'].sum()
        
        c1.metric("Balance Real", f"{balance_actual:,.2f} €")
        
        win_rate = (len(df_trades[df_trades['net_profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        
        pos_sum = df_trades[df_trades['net_profit'] > 0]['net_profit'].sum()
        neg_sum = abs(df_trades[df_trades['net_profit'] < 0]['net_profit'].sum())
        pf = pos_sum/neg_sum if neg_sum != 0 else 0
        c3.metric("Profit Factor", f"{pf:.2f}")
        c4.metric("Operaciones", len(df_trades))

        fig_equity = px.area(df_all, x='closetime', y='equity', color_discrete_sequence=['#E1B12C'])
        fig_equity.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_equity, use_container_width=True)

    elif menu == "🤖 Flota de Bots":
        st.title("🧬 Análisis de la Flota")
        
        # Agrupamos por net_profit para incluir comisiones en el rendimiento del bot
        bot_stats = df_trades[df_trades['magic'] > 0].groupby(['magic', 'bot_name'])['net_profit'].sum().reset_index()
        
        # 1. Gráfico Donut
        fig_donut = px.pie(
            bot_stats, values=abs(bot_stats['net_profit']), names='bot_name', 
            hole=0.5, height=450,
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_donut.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)
        
        st.markdown("---")
        
        # 2. Columnas: Positivos vs Negativos
        col_pos, col_neg = st.columns(2)
        
        with col_pos:
            st.markdown('<p class="column-title">🏆 Ganadores (Neto)</p>', unsafe_allow_html=True)
            ganadores = bot_stats[bot_stats['net_profit'] >= 0].sort_values(by='net_profit', ascending=False)
            if ganadores.empty:
                st.caption("No hay bots en positivo.")
            for _, row in ganadores.iterrows():
                st.markdown(f"""
                <div class="bot-card" style="border-left-color: #00FFC8;">
                    <small style="color:#888;">{row['bot_name']}</small><br>
                    <span class="pos-val">+{row['net_profit']:.2f} €</span>
                </div>
                """, unsafe_allow_html=True)

        with col_neg:
            st.markdown('<p class="column-title">⚠️ En Revisión (Loss)</p>', unsafe_allow_html=True)
            perdedores = bot_stats[bot_stats['net_profit'] < 0].sort_values(by='net_profit', ascending=True)
            if perdedores.empty:
                st.caption("No hay bots en pérdida.")
            for _, row in perdedores.iterrows():
                st.markdown(f"""
                <div class="bot-card" style="border-left-color: #FF4B4B;">
                    <small style="color:#888;">{row['bot_name']}</small><br>
                    <span class="neg-val">{row['net_profit']:.2f} €</span>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "📜 El Grimorio":
        st.title("📜 Registro de Operaciones")
        # Incluimos comisión y swap en la vista detallada para total transparencia
        st.dataframe(df_all[['closetime', 'bot_name', 'symbol', 'type', 'profit', 'commission', 'swap', 'comment']]
                     .sort_values('closetime', ascending=False), 
                     use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564;'>© 2026 Ahharyu Alchemic Trading Labs</p>", unsafe_allow_html=True)

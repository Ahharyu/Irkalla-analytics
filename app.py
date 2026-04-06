import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# --- 1. CONFIGURACIÓN E IDENTIDAD VISUAL ---
st.set_page_config(
    page_title="Ahharyu Alchemic Labs", 
    layout="wide", 
    page_icon="🧪"
)

# INYECCIÓN DE CSS AGRESIVO PARA ELIMINAR CÍRCULOS
st.markdown("""
    <style>
    /* Fondo General */
    .main { background-color: #0E1117; }
    
    /* Contenedor del Logo */
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 20px; }
    .sidebar-logo img { width: 150px; border-radius: 12px; border: 1px solid #E1B12C; padding: 5px; }

    /* ELIMINACIÓN TOTAL DE BOLITAS (RADIO BUTTONS) */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { display: none; } /* Oculta el título 'SISTEMA' */
    
    /* Ocultar el círculo físico del radio */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] :first-child {
        display: none;
    }
    
    /* Convertir el texto en un botón elegante */
    [data-testid="stSidebar"] label[data-baseweb="radio"] {
        background-color: #1A1E26 !important;
        padding: 12px 20px !important;
        border-radius: 10px !important;
        border: 1px solid #333 !important;
        margin-bottom: 8px !important;
        transition: 0.3s !important;
        display: block !important;
        width: 100% !important;
    }

    /* Efecto cuando pasas el ratón o seleccionas */
    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        border-color: #E1B12C !important;
        background-color: #252A34 !important;
    }

    /* Color del texto del menú */
    [data-testid="stSidebar"] label[data-baseweb="radio"] div div {
        color: #BEC3C9 !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    /* Métrica Estilo Dashboard */
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 20px;
        border-radius: 15px;
        border-bottom: 4px solid #E1B12C;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    }

    /* Tarjetas de la Flota de Bots */
    .bot-card { 
        background: #161A22; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        border-left: 6px solid; 
    }
    .pos-val { color: #00FFC8; font-weight: bold; font-size: 1.2em; }
    .neg-val { color: #FF4B4B; font-weight: bold; font-size: 1.2em; }
    .column-title { 
        text-align: center; 
        font-weight: bold; 
        color: #E1B12C; 
        margin-bottom: 25px; 
        text-transform: uppercase; 
        letter-spacing: 2px;
        border-bottom: 1px solid #333;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN Y DATOS ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=10)
def load_data():
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        for col in ['profit', 'commission', 'swap']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        nombres_bots = {0: "Sistema/Balance"}
        df['bot_name'] = df['magic'].map(nombres_bots).fillna("Robot: " + df['magic'].astype(str))
        df['equity'] = df['net_profit'].cumsum()
        df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
        return df, df_trades
    return pd.DataFrame(), pd.DataFrame()

df_all, df_trades = load_data()

# --- 3. BARRA LATERAL (MENÚ BOTONES) ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #E1B12C; margin-top:-10px; letter-spacing: 2px;'>AHHARYU</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #5D6D7E; font-size: 11px; margin-top:-15px;'>ALCHEMIC TRADING LABS</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # El radio button ahora se comporta como botones gracias al CSS
    menu = st.radio(
        "SISTEMA",
        ["🏠 PANEL DE CONTROL", "🤖 FLOTA DE BOTS", "📜 EL GRIMORIO"]
    )
    
    st.markdown("---")
    st.markdown("<div style='text-align: center;'><small style='color: #27AE60;'>● Sincronización Online</small></div>", unsafe_allow_html=True)

# --- 4. SECCIONES ---
if df_all.empty:
    st.info("Laboratorio en espera de datos...")
else:
    if menu == "🏠 PANEL DE CONTROL":
        st.title("⚡ Centro de Mando")
        c1, c2, c3, c4 = st.columns(4)
        balance_actual = df_all['net_profit'].sum()
        c1.metric("Balance Neto", f"{balance_actual:,.2f} €")
        win_rate = (len(df_trades[df_trades['net_profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        pos_sum = df_trades[df_trades['net_profit'] > 0]['net_profit'].sum()
        neg_sum = abs(df_trades[df_trades['net_profit'] < 0]['net_profit'].sum())
        pf = pos_sum/neg_sum if neg_sum != 0 else 0
        c3.metric("Profit Factor", f"{pf:.2f}")
        c4.metric("Operaciones", len(df_trades))

        st.divider()
        st.subheader("📈 Equidad Real")
        st.plotly_chart(px.area(df_all, x='closetime', y='equity', color_discrete_sequence=['#E1B12C']).update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)

    elif menu == "🤖 FLOTA DE BOTS":
        st.title("🧬 Análisis de Transmutación")
        bot_stats = df_trades.groupby(['magic', 'bot_name'])['net_profit'].sum().reset_index()
        st.plotly_chart(px.pie(bot_stats, values=abs(bot_stats['net_profit']), names='bot_name', hole=0.6, height=450, color_discrete_sequence=px.colors.qualitative.Antique).update_layout(template="plotly_dark"), use_container_width=True)
        
        st.divider()
        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.markdown('<p class="column-title">🏆 Ganadores</p>', unsafe_allow_html=True)
            for _, row in bot_stats[bot_stats['net_profit'] >= 0].iterrows():
                st.markdown(f'<div class="bot-card" style="border-left-color: #00FFC8;"><small>{row["bot_name"]}</small><br><span class="pos-val">+{row["net_profit"]:,.2f} €</span></div>', unsafe_allow_html=True)
        with col_neg:
            st.markdown('<p class="column-title">⚠️ En Revisión</p>', unsafe_allow_html=True)
            for _, row in bot_stats[bot_stats['net_profit'] < 0].iterrows():
                st.markdown(f'<div class="bot-card" style="border-left-color: #FF4B4B;"><small>{row["bot_name"]}</small><br><span class="neg-val">{row["net_profit"]:,.2f} €</span></div>', unsafe_allow_html=True)

    elif menu == "📜 EL GRIMORIO":
        st.title("📜 El Grimorio")
        st.dataframe(df_all[['closetime', 'bot_name', 'symbol', 'type', 'profit', 'commission', 'swap', 'comment']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564; font-size: 12px;'>© 2026 Ahharyu Alchemic Trading Labs</p>", unsafe_allow_html=True)

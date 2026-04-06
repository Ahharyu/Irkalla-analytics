import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# DICCIONARIO DE NOMBRES
nombres_bots = {
    0: "Sistema/Balance",
}

# CSS ESTABLE
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 10px; }
    .sidebar-logo img { width: 140px; border-radius: 10px; border: 1px solid #E1B12C; }
    .firm-name { text-align: center; color: #E1B12C; font-family: 'Courier New', Courier, monospace; letter-spacing: 4px; margin-top: 10px; font-weight: bold; }
    .firm-sub { text-align: center; color: #5D6D7E; font-size: 10px; letter-spacing: 1px; margin-bottom: 20px; }

    /* MENU LATERAL */
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label {
        background-color: #1A1E26 !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        width: 100% !important;
        transition: 0.3s;
        margin-bottom: 5px;
    }
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:hover {
        border-color: #E1B12C !important;
        background-color: #252A34 !important;
    }
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        color: #BEC3C9 !important;
        font-weight: bold !important;
    }

    /* METRICAS */
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 20px;
        border-radius: 12px;
        border-bottom: 4px solid #E1B12C;
    }

    /* TARJETAS DE BOTS */
    .bot-card { background:#1E232D; padding:15px; border-radius:10px; margin-bottom:10px; border-left:6px solid; }
    .pos-val { color: #00FFC8; font-weight: bold; }
    .neg-val { color: #FF4B4B; font-weight: bold; }
    .column-title { text-align: center; font-weight: bold; color: #E1B12C; text-transform: uppercase; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CREDENCIALES (RE-VERIFICADAS) ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
# Asegúrate de que esta llave se pegue completa sin saltos de línea extraños
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

# Inicialización segura
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error crítico de conexión: {e}")

@st.cache_data(ttl=10)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # Limpieza numérica
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values('closetime')
            
            # Resultado Neto Real
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            df['bot_name'] = df['magic'].map(nombres_bots).fillna("Bot: " + df['magic'].astype(str))
            
            # --- LÓGICA DE CURVAS PARA EL GRÁFICO SERIO ---
            # Calculamos la equity acumulada por cada bot individualmente
            df['equity_individual'] = df.groupby('bot_name')['net_profit'].cumsum()
            
            # Para la línea TOTAL, necesitamos la suma de todos en cada punto del tiempo
            df['total_account_equity'] = df['net_profit'].cumsum()
            
            df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
            return df, df_trades
    except Exception as e:
        st.error(f"Error consultando Supabase: {e}")
    return pd.DataFrame(), pd.DataFrame()

df_all, df_trades = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown('<div class="firm-name">AHHARYU</div>', unsafe_allow_html=True)
    st.markdown('<div class="firm-sub">ALCHEMIC TRADING LABS</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio("SISTEMA", ["🏠 DASHBOARD", "🤖 FLOTA DE BOTS", "📜 EL GRIMORIO"], label_visibility="collapsed")
    
    st.markdown("---")
    st.success("CONEXIÓN ACTIVA")

# --- 4. SECCIONES ---
if df_all.empty:
    st.info("Sincronizando el laboratorio con el servidor central...")
else:
    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3, c4 = st.columns(4)
        balance_actual = df_all['net_profit'].sum()
        c1.metric("Balance Real", f"{balance_actual:,.2f} €")
        
        win_rate = (len(df_trades[df_trades['net_profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        
        pos_sum = df_trades[df_trades['net_profit'] > 0]['net_profit'].sum()
        neg_sum = abs(df_trades[df_trades['net_profit'] < 0]['net_profit'].sum())
        pf = pos_sum/neg_sum if neg_sum != 0 else 0
        c3.metric("Profit Factor", f"{pf:.2f}")
        c4.metric("Operaciones", len(df_trades))

        st.divider()
        
        # --- GRÁFICO INSTITUCIONAL MEJORADO ---
        st.subheader("📈 Rendimiento Histórico por Activo / Bot")
        
        # Preparamos los datos para que Plotly pinte líneas separadas
        # Primero la Equidad Total (Diferenciada)
        fig = px.line(df_all, x='closetime', y='total_account_equity', 
                      title='Equidad Total de la Cuenta',
                      color_discrete_sequence=['#E1B12C']) # Color Oro
        
        # Añadimos las líneas de los bots individuales para comparar
        for bot in df_all['bot_name'].unique():
            bot_data = df_all[df_all['bot_name'] == bot]
            fig.add_scatter(x=bot_data['closetime'], y=bot_data['equity_individual'], 
                            mode='lines', name=bot, line=dict(width=1.5, dash='dot'))

        fig.update_layout(
            template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)

    elif menu == "🤖 FLOTA DE BOTS":
        st.title("🧬 Análisis de la Flota")
        bot_stats = df_trades.groupby(['magic', 'bot_name'])['net_profit'].sum().reset_index()
        fig_donut = px.pie(bot_stats, values=abs(bot_stats['net_profit']), names='bot_name', hole=0.5, height=400).update_layout(template="plotly_dark")
        st.plotly_chart(fig_donut, use_container_width=True)
        
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
st.markdown("<p style='text-align: center; color: #4E5564;'>© 2026 Ahharyu Alchemic Trading Labs</p>", unsafe_allow_html=True)

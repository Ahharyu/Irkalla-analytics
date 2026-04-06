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

# INYECCIÓN DE CSS AVANZADO (Diseño de Terminal)
st.markdown("""
    <style>
    /* Fondo General */
    .main { background-color: #0E1117; }
    
    /* Contenedor del Logo */
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 20px; }
    .sidebar-logo img { width: 150px; border-radius: 12px; border: 2px solid #E1B12C; padding: 5px; }

    /* METRICAS ESTILO DASHBOARD */
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 20px;
        border-radius: 15px;
        border-bottom: 4px solid #E1B12C;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    }
    div[data-testid="stMetricValue"] { font-size: 24px !important; color: #FFFFFF; }
    div[data-testid="stMetricLabel"] { color: #E1B12C !important; letter-spacing: 1px; font-weight: bold; }

    /* MENÚ LATERAL: ADIÓS BOLITAS (Estilo Botones) */
    div.row-widget.stRadio > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    div.row-widget.stRadio [data-testid="stWidgetLabel"] { display: none; } /* Oculta el título del radio */

    /* Estilo de cada opción del menú */
    div.row-widget.stRadio label {
        background-color: #1A1E26;
        border: 1px solid #333;
        padding: 15px 20px !important;
        border-radius: 10px !important;
        margin-bottom: 10px !important;
        transition: all 0.3s ease;
        width: 100%;
        display: block;
    }

    /* Efecto Hover y Selección */
    div.row-widget.stRadio label:hover {
        border-color: #E1B12C;
        background-color: #252A34;
        cursor: pointer;
    }

    /* Ocultar el círculo nativo de Streamlit */
    div.row-widget.stRadio [data-testid="stMarkdownContainer"] p {
        color: #BEC3C9;
        font-weight: 500;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Tarjetas de la Flota de Bots */
    .bot-card { 
        background: #161A22; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        border-left: 6px solid; 
        box-shadow: 4px 4px 10px rgba(0,0,0,0.2); 
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
        # Asegurar precisión numérica en todas las columnas financieras
        for col in ['profit', 'commission', 'swap']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        
        # Resultado NETO por operación (Balance Real)
        df['net_profit'] = df['profit'] + df['commission'] + df['swap']
        
        # Mapeo de nombres (puedes añadir más IDs aquí)
        nombres_bots = {0: "Sistema/Balance"}
        df['bot_name'] = df['magic'].map(nombres_bots).fillna("Robot Magic: " + df['magic'].astype(str))
        
        # Equity Curve acumulada
        df['equity'] = df['net_profit'].cumsum()
        
        # Filtrar trades de trading (excluyendo el balance inicial si es type 'BALANCE')
        df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
        return df, df_trades
    return pd.DataFrame(), pd.DataFrame()

df_all, df_trades = load_data()

# --- 3. BARRA LATERAL (MENÚ PROFESIONAL) ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #E1B12C; margin-top:-10px; letter-spacing: 2px;'>AHHARYU</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #5D6D7E; font-size: 11px; margin-top:-15px;'>ALCHEMIC TRADING LABS</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Menú estilo navegación limpia
    menu = st.radio(
        "SISTEMA DE NAVEGACIÓN",
        ["🏠 PANEL DE CONTROL", "🤖 FLOTA DE BOTS", "📜 EL GRIMORIO"],
        label_visibility="collapsed" # Ocultamos el label para usar el estilo de botones
    )
    
    st.markdown("---")
    st.markdown("<div style='text-align: center;'><small style='color: #27AE60;'>● Sincronización Online</small></div>", unsafe_allow_html=True)

# --- 4. CONTENIDO DE LAS SECCIONES ---

if df_all.empty:
    st.info("Esperando la señal de los laboratorios (Irkalla.mq5)...")
else:
    if menu == "🏠 PANEL DE CONTROL":
        st.title("⚡ Centro de Mando")
        
        # MÉTRICAS SUPERIORES
        c1, c2, c3, c4 = st.columns(4)
        balance_actual = df_all['net_profit'].sum()
        c1.metric("Balance Neto Actual", f"{balance_actual:,.2f} €")
        
        win_rate = (len(df_trades[df_trades['net_profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        c2.metric("Tasa de Éxito", f"{win_rate:.1f}%")
        
        # Profit Factor
        pos_sum = df_trades[df_trades['net_profit'] > 0]['net_profit'].sum()
        neg_sum = abs(df_trades[df_trades['net_profit'] < 0]['net_profit'].sum())
        pf = pos_sum/neg_sum if neg_sum != 0 else 0
        c3.metric("Profit Factor", f"{pf:.2f}")
        
        c4.metric("Operaciones Totales", len(df_trades))

        st.divider()

        # GRÁFICO DE EQUITY
        st.subheader("📈 Curva de Equidad Real (Profit + Comm + Swap)")
        fig_equity = px.area(df_all, x='closetime', y='equity', color_discrete_sequence=['#E1B12C'])
        fig_equity.update_layout(
            template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Tiempo",
            yaxis_title="Capital (€)"
        )
        st.plotly_chart(fig_equity, use_container_width=True)

    elif menu == "🤖 FLOTA DE BOTS":
        st.title("🧬 Análisis de Transmutación")
        
        # Estadísticas por Bot (Magic Number)
        bot_stats = df_trades.groupby(['magic', 'bot_name'])['net_profit'].sum().reset_index()
        
        # Donut de Activos Real
        fig_donut = px.pie(
            bot_stats, values=abs(bot_stats['net_profit']), names='bot_name', 
            hole=0.6, height=450,
            color_discrete_sequence=px.colors.qualitative.Antique
        )
        fig_donut.update_layout(template="plotly_dark", showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)
        
        st.divider()
        
        # Columnas Ganadores vs Perdedores
        col_pos, col_neg = st.columns(2)
        
        with col_pos:
            st.markdown('<p class="column-title">🏆 Bots en Ganancia</p>', unsafe_allow_html=True)
            ganadores = bot_stats[bot_stats['net_profit'] >= 0].sort_values(by='net_profit', ascending=False)
            for _, row in ganadores.iterrows():
                st.markdown(f"""
                <div class="bot-card" style="border-left-color: #00FFC8;">
                    <small style="color:#888;">{row['bot_name']}</small><br>
                    <span class="pos-val">+{row['net_profit']:,.2f} €</span>
                </div>
                """, unsafe_allow_html=True)

        with col_neg:
            st.markdown('<p class="column-title">⚠️ Bots en Revisión</p>', unsafe_allow_html=True)
            perdedores = bot_stats[bot_stats['net_profit'] < 0].sort_values(by='net_profit', ascending=True)
            for _, row in perdedores.iterrows():
                st.markdown(f"""
                <div class="bot-card" style="border-left-color: #FF4B4B;">
                    <small style="color:#888;">{row['bot_name']}</small><br>
                    <span class="neg-val">{row['net_profit']:,.2f} €</span>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "📜 EL GRIMORIO":
        st.title("📜 Libro de Operaciones")
        # Tabla detallada con todas las columnas financieras
        st.dataframe(
            df_all[['closetime', 'bot_name', 'symbol', 'type', 'profit', 'commission', 'swap', 'comment']]
            .sort_values('closetime', ascending=False), 
            use_container_width=True, 
            hide_index=True
        )

# FOOTER FINAL
st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564; font-size: 12px;'>© 2026 Ahharyu Alchemic Trading Labs | Control de Equidad v4.2</p>", unsafe_allow_html=True)

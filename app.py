import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE PÁGINA E IDENTIDAD ---
st.set_page_config(
    page_title="Ahharyu Alchemic Trading Labs",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para eliminar la sobriedad (Modo Dark Alchemist)
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00FFC8 !important; }
    [data-testid="stMetricLabel"] { color: #E1B12C !important; font-weight: bold; }
    .stDataFrame { border: 1px solid #1E2129; border-radius: 10px; }
    /* Estilo para las tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 15px 20px;
        border-radius: 12px;
        border-left: 5px solid #E1B12C;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN A DATOS ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def get_data():
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        df['equity'] = df['profit'].cumsum()
        # Limpieza de nombres temporal (hasta el mapeo manual)
        df['display_name'] = df['magic'].astype(str) # Por ahora usamos el ID
    return df

df = get_data()

# --- 3. BARRA LATERAL (MENÚ DE NAVEGACIÓN) ---
with st.sidebar:
    # Espacio para tu logo (Sube logo.png a GitHub)
    st.image("https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo empresa.png", width=180)
    st.markdown("<h2 style='text-align: center; color: #E1B12C;'>Ahharyu Labs</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio(
        "Secciones del Laboratorio",
        ["🏠 Panel de Control", "🤖 Flota de Bots", "📜 El Grimorio"],
        index=0
    )
    
    st.markdown("---")
    st.caption("Estado del Sistema: **Live** 🟢")
    st.caption("Firma: Ahharyu Alchemic Trading Labs")

# --- 4. LÓGICA DE PÁGINAS ---

if df.empty:
    st.info("Esperando la primera transmutación de datos desde MT5...")
else:
    if menu == "🏠 Panel de Control":
        st.title("⚡ Dashboard Ejecutivo")
        
        # Fila de métricas clave (Tarjetas)
        m1, m2, m3, m4 = st.columns(4)
        total_profit = df['profit'].sum()
        win_rate = (len(df[df['profit'] > 0]) / len(df)) * 100
        
        m1.metric("Balance Neto", f"{total_profit:.2f} €")
        m2.metric("Win Rate", f"{win_rate:.1f}%")
        m3.metric("Profit Factor", f"{abs(df[df['profit']>0]['profit'].sum() / df[df['profit']<0]['profit'].sum()):.2f}")
        m4.metric("Total Trades", len(df))

        # Gráfico de Equity (Crecimiento)
        st.markdown("### Curva de Crecimiento Alquímico")
        fig_equity = px.area(df, x='closetime', y='equity', 
                             color_discrete_sequence=['#00FFC8'])
        fig_equity.update_layout(
            template="plotly_dark", 
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title=None, yaxis_title="Euros (€)"
        )
        st.plotly_chart(fig_equity, use_container_width=True)

    elif menu == "🤖 Flota de Bots":
        st.title("🧬 Análisis de Estrategias")
        
        # Gráfico comparativo de Bots
        bot_stats = df.groupby('magic')['profit'].sum().reset_index()
        bot_stats = bot_stats.sort_values('profit', ascending=False)

        st.markdown("### Rendimiento por Magic Number")
        fig_bots = px.bar(bot_stats, x='magic', y='profit', 
                          color='profit', color_continuous_scale='Viridis')
        fig_bots.update_layout(template="plotly_dark", xaxis_type='category')
        st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 El Grimorio":
        st.title("📜 Historial de Operaciones")
        st.markdown("Filtra y audita cada trade ejecutado por la firma.")
        
        # Tabla profesional con filtros automáticos de Streamlit
        st.dataframe(
            df[['closetime', 'symbol', 'type', 'magic', 'profit', 'comment']].sort_values('closetime', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# --- 5. FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564;'>© 2024 Ahharyu Alchemic Trading Labs | Enfoque & Precisión</p>", unsafe_allow_html=True)

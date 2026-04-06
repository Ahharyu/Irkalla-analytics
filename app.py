import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Ahharyu Alchemic Trading Labs",
    page_icon="🧪",
    layout="wide"
)

# Estilo para mejorar la visualización de métricas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; }
    .main { background-color: #0E1117; }
    </style>
    """, unsafe_allow_html=True)

# 2. CREDENCIALES
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# 3. CARGA DE DATOS
@st.cache_data(ttl=10)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # Conversión de columnas financieras (las 9 columnas)
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df['closetime'] = pd.to_datetime(df['closetime'])
            # Resultado neto por operación
            df['net_result'] = df['profit'] + df['commission'] + df['swap']
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = load_data()

# 4. SIDEBAR (Navegación y Logo)
with st.sidebar:
    # Intenta cargar el logo desde la raíz del repositorio de GitHub
    if os.path.exists("logo empresa.png"):
        st.image("logo.png", width=180)
    else:
        st.title("🧪 Ahharyu Labs")
    
    st.markdown("---")
    menu = st.radio(
        "Secciones",
        ["📊 Dashboard Principal", "🤖 Análisis de Bots", "📜 Historial Completo"]
    )
    st.divider()
    st.caption("Firma: Ahharyu Alchemic Trading Labs")
    st.caption("v4.0 - Sincronización Total")

# --- LÓGICA DE PANTALLAS ---

if not df.empty:
    # Cálculos globales para las métricas superiores
    total_neto = df['net_result'].sum()
    total_bruto = df['profit'].sum()
    total_gastos = df['commission'].sum() + df['swap'].sum()

    if menu == "📊 Dashboard Principal":
        st.header("🧪 Estado de la Alquimia Financiera")
        
        # Bloque de métricas destacadas
        m1, m2, m3 = st.columns(3)
        m1.metric("BALANCE NETO (EQUITY)", f"{total_neto:,.2f} €")
        m2.metric("BENEFICIO BRUTO", f"{total_bruto:,.2f} €")
        m3.metric("COMISIONES + SWAPS", f"{total_gastos:,.2f} €", delta_color="inverse")

        st.divider()

        # Gráficos principales
        col_graf, col_donut = st.columns([2, 1])

        with col_graf:
            st.subheader("📈 Curva de Crecimiento")
            df_sorted = df.sort_values('closetime')
            df_sorted['cumulative_balance'] = df_sorted['net_result'].cumsum()
            fig_equity = px.line(df_sorted, x='closetime', y='cumulative_balance', 
                                 template="plotly_dark", color_discrete_sequence=['#00e676'])
            st.plotly_chart(fig_equity, use_container_width=True)

        with col_donut:
            st.subheader("🍩 Distribución por Activo")
            # Ignoramos la fila de BALANCE para el gráfico de activos
            df_trades = df[df['type'] != 'BALANCE']
            if not df_trades.empty:
                fig_donut = px.pie(df_trades, names='symbol', values='net_result', 
                                   hole=0.6, template="plotly_dark")
                st.plotly_chart(fig_donut, use_container_width=True)

    elif menu == "🤖 Análisis de Bots":
        st.header("🤖 Rendimiento por Robot (Magic Number)")
        
        # Agrupación estadística por Bot
        bots = df.groupby('magic').agg({
            'net_result': 'sum',
            'commission': 'sum',
            'swap': 'sum',
            'ticket': 'count'
        }).reset_index()
        bots.columns = ['ID Bot (Magic)', 'Profit Neto', 'Comisiones', 'Swaps', 'Operaciones']
        
        st.table(bots.style.format({
            'Profit Neto': '{:,.2f} €',
            'Comisiones': '{:,.2f} €',
            'Swaps': '{:,.2f} €'
        }))

    elif menu == "📜 Historial Completo":
        st.header("📜 Libro de Registros Alquímicos")
        # Mostrar el historial ordenado por fecha de cierre
        st.dataframe(df.sort_values('closetime', ascending=False), use_container_width=True)

else:
    st.warning("⚠️ Sin datos detectados. El sistema está a la espera de registros desde MT5.")

# Pie de página lateral
st.sidebar.markdown("---")
st.sidebar.info("Conexión: Supabase v1.0.4")

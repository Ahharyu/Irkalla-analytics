import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px

# 1. CONFIGURACIÓN E IDIOMA
st.set_page_config(
    page_title="Ahharyu Alchemic Trading Labs",
    page_icon="🧪",
    layout="wide"
)

# 2. CONEXIÓN A SUPABASE
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# 3. CARGA Y LIMPIEZA DE DATOS
@st.cache_data(ttl=10)
def load_all_trades():
    try:
        response = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Asegurar que todas las columnas críticas sean numéricas
            cols = ['profit', 'commission', 'swap', 'magic']
            for c in cols:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
            if 'closetime' in df.columns:
                df['closetime'] = pd.to_datetime(df['closetime'])
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = load_all_trades()

# 4. MENÚ LATERAL (Restaurado)
with st.sidebar:
    st.image("https://www.gstatic.com/lamda/images/favicon_v2_32x32.png", width=50) # Puedes cambiar por tu logo
    st.title("Ahharyu Labs")
    st.markdown("---")
    menu = st.radio(
        "Navegación",
        ["Dashboard General", "Análisis de Operaciones", "Configuración de Bots"]
    )
    st.divider()
    st.info("Estatus: Sincronización Activa ✅")

# --- SECCIÓN: DASHBOARD GENERAL ---
if menu == "Dashboard General":
    st.title("🧪 Panel de Control Alquímico")
    st.subheader("Estado de la Equidad en Tiempo Real")
    
    if not df.empty:
        # CÁLCULO DE BALANCE (Precisión 100,896.69 €)
        # Sumamos Profit (incluye el Balance de 100k) + Comisión + Swap
        total_profit = df['profit'].sum()
        total_comm = df['commission'].sum()
        total_swap = df['swap'].sum()
        balance_final = total_profit + total_comm + total_swap

        # MÉTRICAS PRINCIPALES
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("BALANCE NETO", f"{balance_final:,.2f} €")
        m2.metric("PROFIT BRUTO", f"{total_profit:,.2f} €")
        m3.metric("COMISIONES", f"{total_comm:,.2f} €", delta_color="inverse")
        m4.metric("SWAPS TOTALES", f"{total_swap:,.2f} €", delta_color="inverse")

        st.divider()

        # GRÁFICO DE CRECIMIENTO
        st.write("### 📈 Curva de Crecimiento de Capital")
        df_sorted = df.sort_values('closetime')
        df_sorted['equity_curve'] = (df_sorted['profit'] + df_sorted['commission'] + df_sorted['swap']).cumsum()
        fig = px.area(df_sorted, x='closetime', y='equity_curve', title="Equity Curve (Neto)")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No hay datos disponibles en Supabase.")

# --- SECCIÓN: ANÁLISIS DE OPERACIONES ---
elif menu == "Análisis de Operaciones":
    st.title("📜 Historial de Transmutaciones")
    if not df.empty:
        # Filtros rápidos
        st.write("### Listado Completo")
        st.dataframe(df.sort_values('closetime', ascending=False), use_container_width=True)
    else:
        st.info("Cargando historial...")

# --- SECCIÓN: CONFIGURACIÓN ---
elif menu == "Configuración de Bots":
    st.title("⚙️ Parámetros de la Firma")
    st.write("Empresa: **Ahharyu Alchemic Trading Labs**")
    st.write("Estado de conexión: **Supabase Cloud v1**")
    st.button("Forzar Sincronización Manual")

# FOOTER
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Ahharyu Alchemic Trading Labs")

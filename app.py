import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA (Antes que cualquier otra cosa)
st.set_page_config(
    page_title="Ahharyu Alchemic Trading Labs",
    page_icon="🧪",
    layout="wide"
)

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
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df['closetime'] = pd.to_datetime(df['closetime'])
            df['net_result'] = df['profit'] + df['commission'] + df['swap']
        return df
    except:
        return pd.DataFrame()

df = load_data()

# 4. SIDEBAR - CONTROL DE ERRORES TOTAL
with st.sidebar:
    # Intentar cargar logo, si falla NO rompe la app
    try:
        # Usamos la URL "raw" de tu GitHub para evitar problemas de rutas locales
        logo_url = "https://raw.githubusercontent.com/Ahharyu/irkalla-analytics/main/logo.png"
        st.image(logo_url, width=180)
    except:
        st.title("🧪 Ahharyu Labs")
    
    st.markdown("---")
    menu = st.radio(
        "Navegación",
        ["📊 Dashboard", "🤖 Análisis de Bots", "📜 Historial"]
    )
    st.divider()
    st.caption("Firma: Ahharyu Alchemic Trading Labs")

# --- LÓGICA DE PANTALLAS ---

if not df.empty:
    # Cálculos para métricas
    total_neto = df['net_result'].sum()
    
    if menu == "📊 Dashboard":
        st.header("🧪 Dashboard Principal")
        
        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("BALANCE NETO", f"{total_neto:,.2f} €")
        m2.metric("PROFIT BRUTO", f"{df['profit'].sum():,.2f} €")
        m3.metric("GASTOS (Comm/Swap)", f"{(df['commission'].sum() + df['swap'].sum()):,.2f} €", delta_color="inverse")

        st.divider()

        # Gráficos
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("### 📈 Equidad Acumulada")
            df_s = df.sort_values('closetime')
            df_s['cum'] = df_s['net_result'].cumsum()
            st.plotly_chart(px.line(df_s, x='closetime', y='cum', template="plotly_dark"), use_container_width=True)
        with c2:
            st.write("### 🍩 Activos")
            df_t = df[df['type'] != 'BALANCE']
            st.plotly_chart(px.pie(df_t, names='symbol', values='net_result', hole=0.5, template="plotly_dark"), use_container_width=True)

    elif menu == "🤖 Análisis de Bots":
        st.header("🤖 Rendimiento por Magic Number")
        bots = df.groupby('magic').agg({'net_result': 'sum', 'ticket': 'count'}).reset_index()
        st.table(bots.style.format({'net_result': '{:,.2f} €'}))

    elif menu == "📜 Historial":
        st.header("📜 Registros")
        st.dataframe(df.sort_values('closetime', ascending=False), use_container_width=True)
else:
    st.warning("Esperando datos...")

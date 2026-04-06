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
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        for col in ['profit', 'commission', 'swap', 'magic']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        df['closetime'] = pd.to_datetime(df['closetime'])
        df['net_result'] = df['profit'] + df['commission'] + df['swap']
    return df

df = load_data()

# 4. SIDEBAR CON LOGO DE GITHUB
with st.sidebar:
    # --- CAMBIO CLAVE: LOGO DESDE GITHUB ---
    # Si tu logo se llama 'logo.png', usa "logo.png". 
    # Si está en una carpeta, usa "assets/logo.png"
    logo_path = "logo empresa.png" 
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.write("🧪 **Ahharyu Labs**") # Fallback si el archivo no se encuentra
    
    st.markdown("---")
    menu = st.radio("Navegación", ["📊 Dashboard", "🤖 Análisis por Bot", "📜 Historial"])
    st.divider()
    st.caption("Firma: Ahharyu Alchemic Trading Labs")

# --- LÓGICA DE PANTALLAS ---

if not df.empty:
    if menu == "📊 Dashboard":
        st.header("🧪 Dashboard de Alquimia")
        
        # MÉTRICAS TOP (Corregidas al céntimo)
        total_neto = df['net_result'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("BALANCE NETO", f"{total_neto:,.2f} €")
        m2.metric("BENEFICIO BRUTO", f"{df['profit'].sum():,.2f} €")
        m3.metric("COMISIONES + SWAPS", f"{(df['commission'].sum() + df['swap'].sum()):,.2f} €", delta_color="inverse")

        st.divider()

        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.write("### 📈 Curva de Equidad")
            df_c = df.sort_values('closetime')
            df_c['cum_net'] = df_c['net_result'].cumsum()
            fig_l = px.line(df_c, x='closetime', y='cum_net', template="plotly_dark", color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_l, use_container_width=True)

        with c_right:
            st.write("### 🍩 Activos (Profit Neto)")
            df_trading = df[df['type'] != 'BALANCE']
            fig_p = px.pie(df_trading, names='symbol', values='net_result', hole=0.5, template="plotly_dark")
            st.plotly_chart(fig_p, use_container_width=True)

    elif menu == "🤖 Análisis por Bot":
        st.header("Análisis de Robots (Magic Number)")
        # Agrupación por Magic
        bot_df = df.groupby('magic').agg({
            'net_result': 'sum',
            'commission': 'sum',
            'swap': 'sum',
            'ticket': 'count'
        }).reset_index()
        bot_df.columns = ['ID Bot (Magic)', 'Resultado Neto', 'Comisiones', 'Swaps', 'Operaciones']
        st.table(bot_df.style.format({'Resultado Neto': '{:,.2f} €', 'Comisiones': '{:,.2f} €', 'Swaps': '{:,.2f} €'}))

    elif menu == "📜 Historial":
        st.header("Registros Completos")
        st.dataframe(df.sort_values('closetime', ascending=False), use_container_width=True)

else:
    st.error("No hay datos. Ejecuta Irkalla.mq5 en MT5.")

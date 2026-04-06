import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ahharyu Alchemic Trading Labs", layout="wide")

# --- CREDENCIALES ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60) # Actualiza cada minuto
def load_data():
    # Traemos las 9 columnas de la tabla 'trades'
    response = supabase.table("trades").select("*").execute()
    data = response.data
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # LIMPIEZA Y CONVERSIÓN (Clave para la precisión)
    # Convertimos a numérico y llenamos vacíos con 0
    cols_to_fix = ['profit', 'commission', 'swap']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0.0
            
    return df

# --- INTERFAZ ---
st.title("🧪 Ahharyu Alchemic Trading Labs")
st.subheader("Panel de Control de Firma de Inversión")

df = load_data()

if not df.empty:
    # --- CÁLCULO MAESTRO (Precisión 100,896.69 €) ---
    # Sumamos el profit (que incluye el balance inicial) + gastos
    total_neto = df['profit'].sum() + df['commission'].sum() + df['swap'].sum()
    
    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Balance Total Neto", value=f"{total_neto:,.2f} €")
    
    with col2:
        st.metric(label="Comisiones Totales", value=f"{df['commission'].sum():,.2f} €", delta_color="inverse")
        
    with col3:
        st.metric(label="Swaps Totales", value=f"{df['swap'].sum():,.2f} €")

    with col4:
        # Contamos operaciones reales (sin contar la fila de BALANCE)
        ops_reales = len(df[df['type'] != 'BALANCE'])
        st.metric(label="Operaciones Cerradas", value=ops_reales)

    # --- TABLA DE OPERACIONES ---
    st.write("### 📜 Historial de Transmutaciones")
    # Ordenar por fecha de cierre si la columna existe
    if 'closetime' in df.columns:
        df = df.sort_values(by='closetime', ascending=False)
        
    st.dataframe(df, use_container_width=True)

else:
    st.warning("No hay datos en la base de datos. Ejecuta el script Irkalla.mq5 en MT5.")

# --- FOOTER ---
st.divider()
st.caption("Ahharyu Alchemic Trading Labs - Sistema de Sincronización de Alta Precisión")

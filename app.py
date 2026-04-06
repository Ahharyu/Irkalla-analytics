import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Ahharyu Alchemic Trading Labs", layout="wide")

# 2. CONEXIÓN DIRECTA (Sin intermediarios)
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# 3. EXTRACCIÓN Y LIMPIEZA DE DATOS
@st.cache_data(ttl=10) # Actualización rápida cada 10 segundos
def get_data():
    # Traemos todas las filas sin excepción
    query = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(query.data)
    
    if df.empty:
        return df

    # FORZADO NUMÉRICO (Evita el error de concatenación de texto)
    # Usamos commission con doble 'm' como en tu DB
    for col in ['profit', 'commission', 'swap']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    return df

# 4. INTERFAZ DE USUARIO
st.title("🧪 Ahharyu Alchemic Trading Labs")
st.subheader("Sincronización de Alta Precisión MT5 -> Supabase")

df = get_data()

if not df.empty:
    # --- CÁLCULO ARITMÉTICO PURO ---
    # No hay lógica manual. Sumamos las 3 columnas que afectan al balance.
    # El registro de 100,000€ entra aquí a través de df['profit'].sum()
    
    val_profit = df['profit'].sum()
    val_comm   = df['commission'].sum()
    val_swap   = df['swap'].sum()
    
    # BALANCE FINAL (Debe ser 100,896.69 €)
    balance_final = val_profit + val_comm + val_swap

    # --- BLOQUE DE MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("BALANCE NETO FINAL", f"{balance_final:,.2f} €")
    with c2:
        st.metric("TOTAL PROFIT (Inc. Depósito)", f"{val_profit:,.2f} €")
    with c3:
        # Mostramos la suma de gastos (Comm + Swap)
        gastos_totales = val_comm + val_swap
        st.metric("GASTOS (Comm + Swap)", f"{gastos_totales:,.2f} €", delta_color="inverse")

    st.divider()

    # --- TABLA DE DATOS CRUDA ---
    st.write("### 📊 Registros en Base de Datos")
    # Mostramos las columnas clave para verificar de dónde vienen esos 428€
    st.dataframe(df[['ticket', 'type', 'symbol', 'profit', 'commission', 'swap', 'closetime', 'comment']], 
                 use_container_width=True)

else:
    st.info("Esperando datos de Irkalla.mq5...")

st.caption("Firma: Ahharyu Alchemic Trading Labs | Control de Equidad")

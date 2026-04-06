import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- ESTILO Y CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Trading Labs", layout="wide", page_icon="🧪")

# --- CONEXIÓN ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=5)
def load_data():
    res = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        for col in ['profit', 'commission', 'swap', 'magic']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    return df

# --- INTERFAZ ---
st.title("🧪 Ahharyu Alchemic Trading Labs")
st.divider()

df = load_data()

if not df.empty:
    # EL CÁLCULO TOTAL
    total_neto = df['profit'].sum() + df['commission'].sum() + df['swap'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("BALANCE NETO ACTUAL", f"{total_neto:,.2f} €")
    col2.metric("PROFIT BRUTO", f"{df['profit'].sum():,.2f} €")
    col3.metric("GASTOS (Comm/Swap)", f"{(df['commission'].sum() + df['swap'].sum()):,.2f} €", delta_color="inverse")

    st.write("### 📜 Historial de Transacciones")
    st.dataframe(df.sort_values('closetime', ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Sin datos. Ejecuta Irkalla.mq5 en MT5.")

st.divider()
st.caption("Ahharyu Labs | Sincronización de Alta Precisión")

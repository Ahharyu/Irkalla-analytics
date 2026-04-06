import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ahharyu Alchemic Trading Labs", layout="wide", page_icon="🧪")

# --- CONEXIÓN ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=10)
def get_clean_data():
    response = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(response.data)
    if df.empty: return df
    # Conversión estricta a números
    for c in ['profit', 'commission', 'swap']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
    return df

# --- INTERFAZ ---
st.title("🧪 Ahharyu Alchemic Trading Labs")
st.divider()

df = get_data() if 'get_data' in locals() else get_clean_data()

if not df.empty:
    # LA SUMA TOTAL SIN FILTROS
    total_neto = df['profit'].sum() + df['commission'].sum() + df['swap'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("BALANCE NETO (EQUITY)", f"{total_neto:,.2f} €")
    c2.metric("BENEFICIO BRUTO", f"{df['profit'].sum():,.2f} €")
    c3.metric("COMISIONES Y SWAPS", f"{(df['commission'].sum() + df['swap'].sum()):,.2f} €")

    st.write("### 📜 Historial de Operaciones Sincronizadas")
    st.dataframe(df.sort_values('closetime', ascending=False), use_container_width=True)
else:
    st.warning("Base de datos vacía.")

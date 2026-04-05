import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONEXIÓN (Cámbialo por tus datos de Supabase) ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_datos():
    response = supabase.table("trades").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['closetime'] = pd.to_datetime(df['closetime'])
        df = df.sort_values('closetime')
        # Calculamos la suma acumulada del profit (Equity)
        df['equity'] = df['profit'].cumsum()
    return df

# --- INTERFAZ ---
st.set_page_config(page_title="Irkalla Analytics", layout="wide")
st.title("🏛️ AHHARYU | IRKALLA ANALYTICS")

df = cargar_datos()

if not df.empty:
    # Métricas de cabecera
    total_profit = df['profit'].sum()
    win_rate = (len(df[df['profit'] > 0]) / len(df)) * 100
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Balance Neto", f"{total_profit:.2f} €")
    c2.metric("Operaciones", len(df))
    c3.metric("Efectividad", f"{win_rate:.1f}%")

    # Gráfico Principal
    st.subheader("Evolución del Capital (Live)")
    st.line_chart(df.set_index('closetime')['equity'])

    # Filtro por Bot (Magic Number)
    st.subheader("Rendimiento por Bot")
    # Agrupamos por Magic y sumamos Profit
    bot_stats = df.groupby('magic')['profit'].sum().sort_values(ascending=False)
    st.bar_chart(bot_stats)

    # Tabla detallada
    with st.expander("Ver historial completo"):
        st.dataframe(df.sort_values('closetime', ascending=False))
else:
    st.warning("Todavía no hay datos en la nube. ¡Ejecuta el script de MT5!")
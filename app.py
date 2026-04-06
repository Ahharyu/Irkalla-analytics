import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Ahharyu Alchemic Trading Labs",
    page_icon="🧪",
    layout="wide"
)

# 2. CREDENCIALES (Invisible y Directo)
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# 3. CARGA DE DATOS (9 COLUMNAS)
@st.cache_data(ttl=30)
def fetch_trades():
    try:
        # Traemos todo de la tabla trades
        query = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(query.data)
        
        if df.empty:
            return df

        # CONVERSIÓN FORZOSA A NÚMEROS
        # Esto asegura que commission (doble m), profit y swap no den errores de string
        numeric_cols = ['profit', 'commission', 'swap']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0
        
        # Convertir fecha para ordenar
        if 'closetime' in df.columns:
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values(by='closetime', ascending=False)
            
        return df
    except Exception as e:
        st.error(f"Error en la conexión: {e}")
        return pd.DataFrame()

# 4. INTERFAZ Y CÁLCULOS
st.title("🧪 Ahharyu Alchemic Trading Labs")
st.markdown("---")

df = fetch_trades()

if not df.empty:
    # --- LA MATEMÁTICA DEL DESFASE ---
    # Sumamos ABSOLUTAMENTE TODO lo que hay en las columnas de dinero.
    # El 'profit' del registro BALANCE (los 100k) se suma aquí automáticamente.
    total_profit = df['profit'].sum()
    total_comm   = df['commission'].sum()
    total_swap   = df['swap'].sum()
    
    # El Balance Neto Real que DEBE coincidir con MT5
    balance_final = total_profit + total_comm + total_swap

    # MÉTRICAS EN PANTALLA
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("BALANCE NETO", f"{balance_final:,.2f} €")
    with m2:
        st.metric("PROFITS BRUTOS", f"{total_profit:,.2f} €")
    with m3:
        # Delta rojo si es gasto (comisiones)
        st.metric("COMISIONES", f"{total_comm:,.2f} €", delta_color="inverse")
    with m4:
        st.metric("SWAPS", f"{total_swap:,.2f} €")

    # GRÁFICO DE EVOLUCIÓN (Opcional pero útil)
    st.write("### 📈 Curva de Equidad")
    df_sorted = df.sort_values('closetime')
    # Calculamos el balance acumulado fila a fila
    df_sorted['cumulative_balance'] = (df_sorted['profit'] + df_sorted['commission'] + df_sorted['swap']).cumsum()
    fig = px.line(df_sorted, x='closetime', y='cumulative_balance', title="Evolución del Capital")
    st.plotly_chart(fig, use_container_width=True)

    # TABLA DETALLADA
    st.write("### 📜 Historial de Operaciones")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ No hay datos detectados. Asegúrate de ejecutar Irkalla.mq5 en tu terminal MT5.")

st.caption("Firma: Ahharyu Alchemic Trading Labs | Sincronización en Tiempo Real")

import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide")

# --- 2. CONEXIÓN ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_client()

@st.cache_data(ttl=2)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # LIMPIEZA ABSOLUTA DE DATOS
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # CREACIÓN DEL NETO (Aseguramos que profit sume de verdad)
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            df['closetime'] = pd.to_datetime(df['closetime'])
            return df.sort_values('closetime')
    except: pass
    return pd.DataFrame()

df = load_data()

# --- 3. NAVEGACIÓN ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("No hay datos cargados.")
else:
    # --- 4. CONTABILIDAD SIN FALLO POSIBLE ---
    
    # Balance Actual: La realidad de la cuenta (Suma de todo)
    balance_total = df['net_profit'].sum()
    
    # Depósito: El primer magic 0 (Los 100k)
    df_depo = df[df['magic'] == 0].sort_values('closetime')
    val_deposito = df_depo['net_profit'].iloc[0] if not df_depo.empty else 100000.0
    
    # Profit Bots: Es el Balance actual menos el depósito inicial. PUNTO.
    # Esta es la forma más infalible de calcularlo.
    profit_real_bots = balance_total - val_deposito

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Total", f"{balance_total:,.2f} €")
        c2.metric("Profit Real Bots", f"{profit_real_bots:,.2f} €")
        c3.metric("Capital Inicial", f"{val_deposito:,.2f} €")
        
        st.divider()
        df['equity'] = df['net_profit'].cumsum()
        fig_dash = go.Figure(go.Scatter(x=df['closetime'], y=df['equity'], mode='lines', line=dict(color='#E1B12C', width=2)))
        fig_dash.update_layout(template="plotly_dark", title="Evolución de Cuenta", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dash, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento de Unidades")
        # Aquí solo queremos ver trades de bots (ignorar el depósito)
        # Filtramos por magic != 0 Y ADEMÁS por profit != valor del depósito
        df_bots_solo = df[(df['magic'] != 0) & (df['net_profit'] < 50000)].copy()
        
        if df_bots_solo.empty:
            st.info("Esperando trades de bots...")
        else:
            bot_ids = sorted(df_bots_solo['magic'].unique())
            opcion = st.selectbox("Unidad:", ["📊 TODA LA FLOTA"] + [f"BOT {int(m)}" for m in bot_ids])
            
            fig_bots = go.Figure()
            if opcion == "📊 TODA LA FLOTA":
                for m in bot_ids:
                    b_df = df_bots_solo[df_bots_solo['magic'] == m].copy()
                    # Graficamos el acumulado trade a trade
                    b_df['cum_p'] = b_df['net_profit'].cumsum()
                    fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_p'], name=f"BOT {int(m)}", mode='lines'))
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_bots_solo[df_bots_solo['magic'] == m_id].copy()
                b_df['cum_p'] = b_df['net_profit'].cumsum()
                st.metric("Beneficio Acumulado", f"{b_df['net_profit'].sum():,.2f} €")
                fig_bots.add_trace(go.Scatter(x=b_df['closetime'], y=b_df['cum_p'], name=opcion, mode='lines', line=dict(color='#00FFC8')))

            fig_bots.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro")
        df['tag'] = df['magic'].apply(lambda x: "DEPOSITO" if x == 0 else f"BOT {int(x)}")
        st.dataframe(df[['closetime', 'tag', 'symbol', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# --- 2. CREDENCIALES ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=5) # Reducimos TTL para ver cambios rápidos
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values('closetime')
            
            # Cálculo Neto por operación
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            
            # Identificación
            df['bot_label'] = df['magic'].apply(lambda x: "Balance Sistema" if x==0 else f"BOT {int(x)}")
            
            # Profit acumulado individual por bot (Empezando de 0)
            df['bot_profit_cum'] = df.groupby('magic')['net_profit'].cumsum()
            
            return df
    except: pass
    return pd.DataFrame()

df_all = load_data()

# --- 3. BARRA LATERAL (MENÚ RECUPERADO) ---
with st.sidebar:
    st.markdown(f'<center><img src="{LOGO_URL}" width="140"></center>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#E1B12C;'>AHHARYU</h3>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 INSPECTOR DE BOTS", "📜 HISTORIAL"])

# --- 4. LÓGICA DE CÁLCULO REAL ---
if not df_all.empty:
    # EL BALANCE REAL: Es la suma de TODO lo que hay en la tabla (Depósito + Trades)
    balance_total_real = df_all['net_profit'].sum()
    
    # EL BENEFICIO DE LOS BOTS: Solo trades donde magic NO es 0
    df_solo_bots = df_all[df_all['magic'] != 0].copy()
    beneficio_bots_puro = df_solo_bots['net_profit'].sum()
    
    # DEPÓSITO INICIAL: El valor del magic 0
    deposito_inicial = df_all[df_all['magic'] == 0]['net_profit'].sum()

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        
        # AQUÍ ESTÁ LA CORRECCIÓN: No sumamos 100k manuales. Mostramos lo que dice la DB.
        c1.metric("Balance Total Cuenta", f"{balance_total_real:,.2f} €")
        c2.metric("Beneficio Neto Bots", f"{beneficio_bots_puro:,.2f} €", delta_color="normal")
        c3.metric("Depósito Inicial", f"{deposito_inicial:,.2f} €")
        
        st.divider()
        # Gráfica de crecimiento de la cuenta entera
        df_all['equity_curve'] = df_all['net_profit'].cumsum()
        fig_main = go.Figure(go.Scatter(x=df_all['closetime'], y=df_all['equity_curve'], fill='tozeroy', line=dict(color='#E1B12C')))
        fig_main.update_layout(template="plotly_dark", title="Evolución Total del Capital (€)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_main, use_container_width=True)

    elif menu == "🤖 INSPECTOR DE BOTS":
        st.title("Análisis de la Flota")
        bots_reales = sorted([b for b in df_all['bot_label'].unique() if "BOT" in b])
        opcion = st.selectbox("Unidad:", ["🔍 VER TODOS"] + bots_reales)
        
        fig_bots = go.Figure()
        
        if opcion == "🔍 VER TODOS":
            for b in bots_reales:
                temp_df = df_all[df_all['bot_label'] == b]
                fig_bots.add_trace(go.Scatter(x=temp_df['closetime'], y=temp_df['bot_profit_cum'], name=b))
            st.subheader(f"Rendimiento Combinado: {beneficio_bots_puro:,.2f} €")
        else:
            temp_df = df_all[df_all['bot_label'] == opcion]
            fig_bots.add_trace(go.Scatter(x=temp_df['closetime'], y=temp_df['bot_profit_cum'], name=opcion, fill='tozeroy'))
            st.subheader(f"Rendimiento Individual: {temp_df['net_profit'].sum():,.2f} €")

        fig_bots.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Registro de Operaciones")
        st.dataframe(df_all[['closetime', 'bot_label', 'symbol', 'net_profit', 'comment']].sort_values('closetime', ascending=False), use_container_width=True)

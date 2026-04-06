import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 10px; }
    .sidebar-logo img { width: 140px; border-radius: 10px; border: 1px solid #E1B12C; }
    .info-panel { background-color: #161A22; padding: 15px; border-radius: 5px; border: 1px solid #262730; }
    .info-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #262730; font-size: 13px; }
    .info-label { color: #888; }
    .info-value { color: #EEE; font-weight: bold; }
    .value-pos { color: #00FFC8; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CREDENCIALES ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=10)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values('closetime')
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            
            deposit = 100000.0
            df['growth_pct'] = (df['net_profit'].cumsum() / deposit) * 100
            df['bot_name'] = df['magic'].apply(lambda x: "Sistema" if x==0 else f"Bot {int(x)}")
            
            # Calculamos beneficio acumulado EN EUROS para cada bot
            df['bot_profit_abs'] = df.groupby('bot_name')['net_profit'].cumsum()
            
            return df, deposit
    except: pass
    return pd.DataFrame(), 100000.0

df_all, deposit = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#E1B12C;'>AHHARYU</h3>", unsafe_allow_html=True)
    menu = st.radio("SISTEMA", ["📈 PERFORMANCE", "🤖 BOTS", "📜 LOGS"], label_visibility="collapsed")

# --- 4. SECCIONES ---
if df_all.empty:
    st.info("Sincronizando...")
else:
    if menu == "📈 PERFORMANCE":
        st.title("Advanced Analytics")
        
        col_info, col_graph = st.columns([1, 4])
        
        beneficio_total = df_all['net_profit'].sum()
        gain_pct = (beneficio_total / deposit) * 100
        
        with col_info:
            st.markdown(f"""
                <div class="info-panel">
                    <div class="info-row"><span class="info-label">Ganancia:</span><span class="info-value value-pos">+{gain_pct:.2f}%</span></div>
                    <div class="info-row"><span class="info-label">Saldo:</span><span class="info-value">${deposit+beneficio_total:,.2f}</span></div>
                    <div class="info-row"><span class="info-label">Beneficio:</span><span class="info-value value-pos">${beneficio_total:,.2f}</span></div>
                </div>
            """, unsafe_allow_html=True)

        with col_graph:
            # USAMOS SUBPLOTS CON EJE Y SECUNDARIO
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # 1. LÍNEA ROJA: CRECIMIENTO % DE LA CUENTA (Eje Principal - Izquierda)
            fig.add_trace(go.Scatter(
                x=df_all['closetime'], y=df_all['growth_pct'],
                name="Crecimiento Cuenta (%)",
                line=dict(color='#FF4B4B', width=4),
                fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.05)'
            ), secondary_y=False)

            # 2. LÍNEAS DE BOTS: BENEFICIO EN € (Eje Secundario - Derecha)
            # Esto permite que se vean grandes aunque ganen poco
            for bot in df_all['bot_name'].unique():
                if bot != "Sistema":
                    bot_df = df_all[df_all['bot_name'] == bot]
                    fig.add_trace(go.Scatter(
                        x=bot_df['closetime'], y=bot_df['bot_profit_abs'],
                        name=f"{bot} (€)",
                        line=dict(width=2),
                        opacity=0.8
                    ), secondary_y=True)

            fig.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                height=600,
                legend=dict(orientation="h", y=-0.2),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='#262730'),
            )

            # Configuración de Ejes
            fig.update_yaxes(title_text="<b>Crecimiento Cuenta (%)</b>", color="#FF4B4B", secondary_y=False, showgrid=True, gridcolor='#262730')
            fig.update_yaxes(title_text="<b>Rendimiento Bots (€)</b>", secondary_y=True, showgrid=False)

            st.plotly_chart(fig, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Detalle de la Flota")
        stats = df_all[df_all['magic'] != 0].groupby('bot_name')['net_profit'].sum().reset_index()
        for _, row in stats.iterrows():
            st.metric(row['bot_name'], f"{row['net_profit']:.2f} €")

    elif menu == "📜 LOGS":
        st.dataframe(df_all.sort_values('closetime', ascending=False), use_container_width=True)

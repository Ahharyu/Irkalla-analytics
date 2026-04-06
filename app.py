import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 10px; }
    .sidebar-logo img { width: 140px; border-radius: 10px; border: 1px solid #E1B12C; }
    .bot-stat-card {
        background-color: #161A22;
        border: 1px solid #262730;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-val { font-size: 24px; font-weight: bold; color: #E1B12C; }
    .metric-lbl { font-size: 12px; color: #888; text-transform: uppercase; }
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
            df['bot_label'] = df['magic'].apply(lambda x: "Depósito/Sistema" if x==0 else f"BOT {int(x)}")
            
            # Cálculo de equidad acumulada individual por bot
            df['bot_profit_cum'] = df.groupby('magic')['net_profit'].cumsum()
            
            return df, deposit
    except: pass
    return pd.DataFrame(), 100000.0

df_all, deposit = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#E1B12C;'>AHHARYU</h3>", unsafe_allow_html=True)
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD TOTAL", "🤖 INSPECTOR DE BOTS", "📜 REGISTRO"], label_visibility="collapsed")
    st.markdown("---")
    st.info(f"Capital: {deposit:,.0f} €")

# --- 4. SECCIONES ---
if df_all.empty:
    st.warning("Laboratorio sin datos...")
else:
    if menu == "🏠 DASHBOARD TOTAL":
        st.title("Performance Global")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_all['closetime'], y=df_all['growth_pct'],
            name="Crecimiento (%)", line=dict(color='#FF4B4B', width=3),
            fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.05)'
        ))
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        neto = df_all['net_profit'].sum()
        c1.metric("Beneficio Neto", f"{neto:,.2f} €")
        c2.metric("Balance Total", f"{deposit+neto:,.2f} €")
        c3.metric("Crecimiento", f"{(neto/deposit)*100:.3f} %")

    elif menu == "🤖 INSPECTOR DE BOTS":
        st.title("Análisis de la Flota")
        
        # Filtramos para no mostrar el Magic 0
        bots_reales = [b for b in df_all['bot_label'].unique() if "BOT" in b]
        
        # AÑADIMOS LA OPCIÓN "TODOS"
        opciones = ["🔍 VER TODA LA FLOTA"] + bots_reales
        selected_bot = st.selectbox("Seleccionar unidad:", opciones)
        
        fig_bots = go.Figure()

        if selected_bot == "🔍 VER TODA LA FLOTA":
            st.subheader("Rendimiento Comparativo (Profit Neto)")
            # Pintamos una línea por cada bot real
            for bot in bots_reales:
                bot_df = df_all[df_all['bot_label'] == bot]
                fig_bots.add_trace(go.Scatter(
                    x=bot_df['closetime'], 
                    y=bot_df['bot_profit_cum'],
                    mode='lines',
                    name=bot,
                    line=dict(width=2)
                ))
            
            # Métricas generales de la suma de los bots
            neto_bots = df_all[df_all['magic'] != 0]['net_profit'].sum()
            st.info(f"Beneficio acumulado de todos los bots: {neto_bots:,.2f} €")

        else:
            # Vista individual (la que ya tenías)
            bot_data = df_all[df_all['bot_label'] == selected_bot].copy()
            
            m1, m2, m3 = st.columns(3)
            profit_bot = bot_data['net_profit'].sum()
            ops = len(bot_data)
            win_rate = (len(bot_data[bot_data['net_profit'] > 0]) / ops * 100) if ops > 0 else 0
            
            m1.markdown(f'<div class="bot-stat-card"><p class="metric-lbl">Beneficio</p><p class="metric-val">{profit_bot:,.2f}€</p></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="bot-stat-card"><p class="metric-lbl">Operaciones</p><p class="metric-val">{ops}</p></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="bot-stat-card"><p class="metric-lbl">Win Rate</p><p class="metric-val">{win_rate:.1f}%</p></div>', unsafe_allow_html=True)

            fig_bots.add_trace(go.Scatter(
                x=bot_data['closetime'], 
                y=bot_data['bot_profit_cum'],
                mode='lines+markers',
                name=selected_bot,
                line=dict(color='#00FFC8', width=3)
            ))

        fig_bots.update_layout(
            template="plotly_dark",
            height=550,
            xaxis_title="Evolución Temporal",
            yaxis_title="Euros (€)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='#262730'),
            yaxis=dict(showgrid=True, gridcolor='#262730'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 REGISTRO":
        st.title("El Grimorio")
        st.dataframe(df_all[['closetime', 'bot_label', 'symbol', 'type', 'net_profit', 'comment']].sort_values('closetime', ascending=False), use_container_width=True)

import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# CSS PARA PANEL DE ESTADÍSTICAS (Lado Izquierdo estilo Myfxbook)
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 10px; }
    .sidebar-logo img { width: 140px; border-radius: 10px; border: 1px solid #E1B12C; }
    
    /* Panel de Info estilo Myfxbook */
    .info-panel {
        background-color: #161A22;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #262730;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        border-bottom: 1px solid #262730;
        font-size: 13px;
    }
    .info-label { color: #888; }
    .info-value { color: #EEE; font-weight: bold; }
    .value-pos { color: #00FFC8; }
    .value-neg { color: #FF4B4B; }
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
            
            # Depósito inicial (Ajusta si es distinto a 100k)
            initial_deposit = 100000.0
            
            # Cálculo de crecimiento acumulado en %
            df['profit_cum'] = df['net_profit'].cumsum()
            df['growth_pct'] = (df['profit_cum'] / initial_deposit) * 100
            
            # Crecimiento por bot
            df['bot_name'] = df['magic'].apply(lambda x: "Sistema" if x==0 else f"Bot: {int(x)}")
            df['bot_profit_cum'] = df.groupby('bot_name')['net_profit'].cumsum()
            df['bot_growth_pct'] = (df['bot_profit_cum'] / initial_deposit) * 100
            
            df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
            return df, df_trades, initial_deposit
    except: pass
    return pd.DataFrame(), pd.DataFrame(), 100000.0

df_all, df_trades, deposit = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#E1B12C;'>AHHARYU</h3>", unsafe_allow_html=True)
    menu = st.radio("SISTEMA", ["📈 CRECIMIENTO", "🤖 FLOTA", "📜 HISTORIAL"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Sincronizado: Online")

# --- 4. SECCIONES ---
if df_all.empty:
    st.info("Esperando telemetría...")
else:
    if menu == "📈 CRECIMIENTO":
        st.title("Performance Analytics")
        
        # Layout: Panel de Info Izquierda + Gráfico Derecha
        col_info, col_graph = st.columns([1, 4])
        
        with col_info:
            st.markdown('<p style="color:#E1B12C; font-weight:bold;">INFO</p>', unsafe_allow_html=True)
            gain = (df_all['net_profit'].sum() / deposit) * 100
            beneficio = df_all['net_profit'].sum()
            
            st.markdown(f"""
                <div class="info-panel">
                    <div class="info-row"><span class="info-label">Ganancia:</span><span class="info-value value-pos">+{gain:.2f}%</span></div>
                    <div class="info-row"><span class="info-label">Abs. Ganancia:</span><span class="info-value value-pos">+{gain:.2f}%</span></div>
                    <div class="info-row"><span class="info-label">Saldo:</span><span class="info-value">${deposit+beneficio:,.2f}</span></div>
                    <div class="info-row"><span class="info-label">Beneficio:</span><span class="info-value value-pos">${beneficio:,.2f}</span></div>
                    <div class="info-row"><span class="info-label">Depósitos:</span><span class="info-value">${deposit:,.0f}</span></div>
                </div>
            """, unsafe_allow_html=True)

        with col_graph:
            # CREACIÓN DEL GRÁFICO PROFESIONAL (Plotly Graph Objects)
            fig = go.Figure()

            # Línea Principal de Crecimiento (Roja como en tu imagen)
            fig.add_trace(go.Scatter(
                x=df_all['closetime'], y=df_all['growth_pct'],
                mode='lines', name='Crecimiento',
                line=dict(color='#FF4B4B', width=3),
                fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.05)'
            ))

            # Añadir líneas finas para los bots (opcional, se pueden apagar en la leyenda)
            for bot in df_all['bot_name'].unique():
                if bot != "Sistema":
                    bot_df = df_all[df_all['bot_name'] == bot]
                    fig.add_trace(go.Scatter(
                        x=bot_df['closetime'], y=bot_df['bot_growth_pct'],
                        mode='lines', name=bot,
                        line=dict(width=1, dash='dot'),
                        visible='legendonly' # Apagados por defecto para no ensuciar
                    ))

            fig.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=30, b=0),
                height=500,
                legend=dict(orientation="h", y=-0.2),
                xaxis=dict(showgrid=True, gridcolor='#262730', zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='#262730', zeroline=False, ticksuffix="%"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "🤖 FLOTA":
        st.title("Análisis por Magic Number")
        # Aquí mantenemos las tarjetas pero con estilo Myfxbook
        stats = df_trades.groupby('bot_name')['net_profit'].sum().reset_index()
        for _, row in stats.iterrows():
            color = "#00FFC8" if row['net_profit'] >= 0 else "#FF4B4B"
            st.markdown(f"""
                <div style="background:#161A22; padding:15px; border-left:5px solid {color}; border-radius:5px; margin-bottom:10px;">
                    <span style="color:#888; font-size:12px;">{row['bot_name']}</span><br>
                    <span style="font-size:18px; font-weight:bold;">${row['net_profit']:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

    elif menu == "📜 HISTORIAL":
        st.title("Historial de Operaciones")
        st.dataframe(df_all[['closetime', 'bot_name', 'symbol', 'type', 'profit', 'net_profit']].sort_values('closetime', ascending=False), use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564; font-size: 10px;'>AHHARYU ALCHEMIC TRADING LABS | V5.0</p>", unsafe_allow_html=True)

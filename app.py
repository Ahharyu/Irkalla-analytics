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
    .info-panel { background-color: #161A22; padding: 15px; border-radius: 5px; border: 1px solid #262730; }
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #262730; font-size: 14px; }
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
            
            # Identificación clara
            df['bot_label'] = df['magic'].apply(lambda x: "Sistema" if x==0 else f"Bot {int(x)}")
            # Acumulado individual (sin importar el balance total)
            df['profit_cum'] = df.groupby('magic')['net_profit'].cumsum()
            
            return df
    except: pass
    return pd.DataFrame()

df_all = load_data()

# --- 3. LÓGICA DE INTERFAZ ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#E1B12C;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Selector de Bot (El "Todos" ahora es el corazón del sistema)
    opciones = ["📊 VER TODA LA FLOTA"] + sorted([b for b in df_all['bot_label'].unique() if "Bot" in b])
    seleccion = st.selectbox("Seleccionar Unidad:", opciones)

# --- 4. CUERPO PRINCIPAL ---
if df_all.empty:
    st.warning("Conectando con el oráculo de datos...")
else:
    # Panel de Estadísticas (Estilo Institucional)
    beneficio_total = df_all['net_profit'].sum()
    deposito_inicial = 100000.0
    balance_final = deposito_inicial + beneficio_total
    rentabilidad = (beneficio_total / deposito_inicial) * 100

    col_stats, col_main = st.columns([1, 3])

    with col_stats:
        st.markdown(f"""
            <div class="info-panel">
                <div class="info-row"><span class="info-label">Ganancia:</span><span class="info-value value-pos">+{rentabilidad:.2f}%</span></div>
                <div class="info-row"><span class="info-label">Abs. Ganancia:</span><span class="info-value value-pos">+{rentabilidad:.2f}%</span></div>
                <div class="info-row"><span class="info-label">Saldo:</span><span class="info-value">{balance_final:,.2f} €</span></div>
                <div class="info-row"><span class="info-label">Beneficio:</span><span class="info-value value-pos">{beneficio_total:,.2f} €</span></div>
                <div class="info-row"><span class="info-label">Depósitos:</span><span class="info-value">{deposito_inicial:,.0f} €</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        # Mostrar trades recientes del bot seleccionado
        st.caption("Últimos Movimientos")
        if seleccion == "📊 VER TODA LA FLOTA":
            mini_df = df_all[df_all['magic'] != 0]
        else:
            mini_df = df_all[df_all['bot_label'] == seleccion]
        st.dataframe(mini_df[['closetime', 'net_profit']].tail(5).sort_values('closetime', ascending=False), hide_index=True)

    with col_main:
        fig = go.Figure()

        if seleccion == "📊 VER TODA LA FLOTA":
            # Línea de crecimiento total de la cuenta en % (Eje secundario oculto para escala)
            # Para no "aplastar", graficamos todos los bots en su profit real
            bots_unicos = [b for b in df_all['bot_label'].unique() if "Bot" in b]
            for bot in bots_unicos:
                bot_df = df_all[df_all['bot_label'] == bot]
                fig.add_trace(go.Scatter(
                    x=bot_df['closetime'], y=bot_df['profit_cum'],
                    name=bot, mode='lines', line=dict(width=2)
                ))
            st.subheader("Análisis Comparativo de Beneficio Neto (€)")
        else:
            # Vista de un solo bot
            bot_df = df_all[df_all['bot_label'] == seleccion]
            fig.add_trace(go.Scatter(
                x=bot_df['closetime'], y=bot_df['profit_cum'],
                name=seleccion, mode='lines+markers',
                line=dict(color='#00FFC8', width=3),
                fill='tozeroy', fillcolor='rgba(0, 255, 200, 0.05)'
            ))
            st.subheader(f"Rendimiento Detallado: {seleccion}")

        fig.update_layout(
            template="plotly_dark",
            height=500,
            hovermode="x unified",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis=dict(showgrid=True, gridcolor='#262730'),
            yaxis=dict(showgrid=True, gridcolor='#262730', title="Euros (€)"),
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564; font-size: 10px;'>AHHARYU ALCHEMIC TRADING LABS | SISTEMA UNIFICADO V7.0</p>", unsafe_allow_html=True)

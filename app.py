import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide", page_icon="🧪")

# DICCIONARIO DE NOMBRES (Añade aquí tus Magic Numbers reales)
nombres_bots = {
    0: "Sistema/Balance",
    # Ejemplo: 12345: "Scalper Pro",
}

# CSS ESTABLE PARA INTERFAZ OSCURA (Mantenemos tu diseño original)
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .sidebar-logo { display: flex; justify-content: center; margin-bottom: 10px; }
    .sidebar-logo img { width: 140px; border-radius: 10px; border: 1px solid #E1B12C; }
    .firm-name { text-align: center; color: #E1B12C; font-family: 'Courier New', Courier, monospace; letter-spacing: 4px; margin-top: 10px; font-weight: bold; }
    .firm-sub { text-align: center; color: #5D6D7E; font-size: 10px; letter-spacing: 1px; margin-bottom: 20px; }

    /* MENU LATERAL: CAJAS INTERACTIVAS */
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label {
        background-color: #1A1E26 !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        width: 100% !important;
        transition: 0.3s;
        margin-bottom: 5px;
    }
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:hover {
        border-color: #E1B12C !important;
        background-color: #252A34 !important;
    }
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        color: #BEC3C9 !important;
        font-weight: bold !important;
    }

    /* METRICAS */
    div[data-testid="stMetric"] {
        background-color: #161A22;
        padding: 20px;
        border-radius: 12px;
        border-bottom: 4px solid #E1B12C;
    }

    /* TARJETAS DE BOTS */
    .bot-card { background:#1E232D; padding:15px; border-radius:10px; margin-bottom:10px; border-left:6px solid; }
    .pos-val { color: #00FFC8; font-weight: bold; }
    .neg-val { color: #FF4B4B; font-weight: bold; }
    .column-title { text-align: center; font-weight: bold; color: #E1B12C; text-transform: uppercase; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CREDENCIALES ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk9MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=10)
def load_data():
    try:
        res = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # Conversión numérica de precisión
            for col in ['profit', 'commission', 'swap', 'magic']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            df['closetime'] = pd.to_datetime(df['closetime'])
            df = df.sort_values('closetime')
            
            # Resultado NETO por operación (Profit + Comm + Swap)
            df['net_profit'] = df['profit'] + df['commission'] + df['swap']
            
            # Mapeo de nombres
            df['bot_name'] = df['magic'].map(nombres_bots).fillna("Bot: " + df['magic'].astype(str))
            
            # --- CÁLCULO DE EQUITY CURVES POR BOT (Precisión Institucional) ---
            # 1. Obtenemos todos los timestamps únicos y Magic Numbers
            all_times = df['closetime'].unique()
            all_times.sort()
            all_magics = df['bot_name'].unique()
            
            # 2. Creamos un DataFrame maestro con todas las combinaciones tiempo/bot
            index = pd.MultiIndex.from_product([all_times, all_magics], names=['closetime', 'bot_name'])
            equity_df = pd.DataFrame(index=index).reset_index()
            
            # 3. Mapeamos el net_profit real a este DataFrame maestro
            trades_grouped = df.groupby(['closetime', 'bot_name'])['net_profit'].sum().reset_index()
            equity_df = pd.merge(equity_df, trades_grouped, on=['closetime', 'bot_name'], how='left').fillna(0.0)
            
            # 4. Calculamos la suma acumulada por cada Bot de forma independiente
            equity_df['equity_bot'] = equity_df.groupby('bot_name')['net_profit'].cumsum()
            
            # 5. Calculamos la Equity Total (suma de todas las equities de los bots en cada momento)
            total_equity_curve = equity_df.groupby('closetime')['equity_bot'].sum().reset_index()
            total_equity_curve['bot_name'] = "EQUIDAD TOTAL DE LA CUENTA" # Nombre especial para identificarla
            total_equity_curve.rename(columns={'equity_bot': 'equity_value'}, inplace=True)
            
            # 6. Preparamos el DataFrame final para el gráfico multi-línea
            # Primero las curvas individuales de los bots
            bots_curves = equity_df[['closetime', 'bot_name', 'equity_bot']].rename(columns={'equity_bot': 'equity_value'})
            
            # Luego concatenamos la curva total
            final_curves_df = pd.concat([bots_curves, total_equity_curve], ignore_index=True)
            
            # Filtramos trades reales para estadísticas
            df_trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
            
            # Necesitamos df_all original para las métricas
            return df, df_trades, final_curves_df
    except Exception as e:
        st.error(f"Error de datos: {e}")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_all, df_trades, df_curves = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown('<div class="firm-name">AHHARYU</div>', unsafe_allow_html=True)
    st.markdown('<div class="firm-sub">ALCHEMIC TRADING LABS</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio("SISTEMA", ["🏠 DASHBOARD", "🤖 FLOTA DE BOTS", "📜 EL GRIMORIO"], label_visibility="collapsed")
    
    st.markdown("---")
    st.success("SISTEMA ONLINE")

# --- 4. SECCIONES ---
if df_all.empty:
    st.info("Sincronizando el laboratorio...")
else:
    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3, c4 = st.columns(4)
        balance_actual = df_all['net_profit'].sum() # Mantenemos el balance real exacto
        c1.metric("Balance Neto Actual", f"{balance_actual:,.2f} €")
        
        win_rate = (len(df_trades[df_trades['net_profit'] > 0]) / len(df_trades) * 100) if not df_trades.empty else 0
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        
        pos_sum = df_trades[df_trades['net_profit'] > 0]['net_profit'].sum()
        neg_sum = abs(df_trades[df_trades['net_profit'] < 0]['net_profit'].sum())
        pf = pos_sum/neg_sum if neg_sum != 0 else 0
        c3.metric("Profit Factor", f"{pf:.2f}")
        c4.metric("Operaciones", len(df_trades))

        st.divider()
        
        # --- NUEVO GRÁFICO INSTITUCIONAL MULTI-LÍNEA ---
        st.subheader("📈 Evolución Comparativa de la Flota (Equidad Real)")
        
        if not df_curves.empty:
            # Usamos Plotly Express para crear el gráfico base
            fig_equity = px.line(df_curves, 
                                 x='closetime', 
                                 y='equity_value', 
                                 color='bot_name', # Una línea por Bot
                                 title="Equity Curves por Bot vs Total de Cuenta",
                                 color_discrete_sequence=px.colors.qualitative.Antique) # Paleta más sobria
            
            # Estilo avanzado para que sea "serio" y profesional
            fig_equity.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    title="Tiempo",
                    showgrid=False,
                    linecolor="#444",
                    mirror=True
                ),
                yaxis=dict(
                    title="Valor de Equidad (€)",
                    showgrid=True,
                    gridcolor="#222", # Rejilla sutil
                    linecolor="#444",
                    mirror=True
                ),
                legend=dict(
                    title="Bots y Cuenta",
                    orientation="h", # Leyenda horizontal abajo para maximizar gráfico
                    yanchor="bottom",
                    y=-0.3, # Posición de la leyenda
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(0,0,0,0.5)", # Fondo leyenda sutil
                    font=dict(size=10, color="# BEC3C9")
                ),
                margin=dict(l=20, r=20, t=50, b=100), # Ajuste márgenes
                hovermode="x unified" # Muestra todos los valores al pasar el ratón por el eje X
            )
            
            # Resaltar la línea del Total (la más importante)
            fig_equity.update_traces(
                selector=dict(name="EQUIDAD TOTAL DE LA CUENTA"), 
                line=dict(color="#E1B12C", width=4) # Oro de Ahharyu, más gruesa
            )
            
            # Líneas más finas para los bots para no saturar
            fig_equity.update_traces(
                line=dict(width=1.5),
                selector=lambda t: t.name != "EQUIDAD TOTAL DE LA CUENTA"
            )

            st.plotly_chart(fig_equity, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para generar las curvas comparativas.")

    elif menu == "🤖 FLOTA DE BOTS":
        st.title("🧬 Análisis de la Flota")
        bot_stats = df_trades.groupby(['magic', 'bot_name'])['net_profit'].sum().reset_index()
        fig_donut = px.pie(bot_stats, values=abs(bot_stats['net_profit']), names='bot_name', hole=0.5, height=400).update_layout(template="plotly_dark")
        st.plotly_chart(fig_donut, use_container_width=True)
        
        st.divider()
        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.markdown('<p class="column-title">🏆 Ganadores</p>', unsafe_allow_html=True)
            for _, row in bot_stats[bot_stats['net_profit'] >= 0].iterrows():
                st.markdown(f'<div class="bot-card" style="border-left-color: #00FFC8;"><small>{row["bot_name"]}</small><br><span class="pos-val">+{row["net_profit"]:,.2f} €</span></div>', unsafe_allow_html=True)
        with col_neg:
            st.markdown('<p class="column-title">⚠️ En Revisión</p>', unsafe_allow_html=True)
            for _, row in bot_stats[bot_stats['net_profit'] < 0].iterrows():
                st.markdown(f'<div class="bot-card" style="border-left-color: #FF4B4B;"><small>{row["bot_name"]}</small><br><span class="neg-val">{row["net_profit"]:,.2f} €</span></div>', unsafe_allow_html=True)

    elif menu == "📜 EL GRIMORIO":
        st.title("📜 El Grimorio")
        st.dataframe(df_all[['closetime', 'bot_name', 'symbol', 'type', 'profit', 'commission', 'swap', 'comment']].sort_values('closetime', ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #4E5564;'>© 2026 Ahharyu Alchemic Trading Labs</p>", unsafe_allow_html=True)

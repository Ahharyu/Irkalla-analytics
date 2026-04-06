import streamlit as st
import pd as pd
from supabase import create_client
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Ahharyu Alchemic Labs", layout="wide")

# --- 2. CONEXIÓN ---
SUPABASE_URL = "https://gnescqvodvrwsyhvymkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImduZXNjcXZvZHZyd3N5aHZ5bWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0MTQ2NTEsImV4cCI6MjA5MDk5MDY1MX0.I1R8YwJHvXE24T09fsp15sWTZohq7iAGDI6FpxLNTqI"
LOGO_URL = "https://raw.githubusercontent.com/ahharyu/irkalla-analytics/main/logo.png"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=2)
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
            return df
    except: pass
    return pd.DataFrame()

df = load_data()

# --- 3. NAVEGACIÓN ---
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.markdown("<h3 style='text-align:center;'>AHHARYU LABS</h3>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("SECCIONES", ["🏠 DASHBOARD", "🤖 BOTS", "📜 HISTORIAL"])

if df.empty:
    st.error("Sincronizando con la red de bots...")
else:
    # MATEMÁTICA DASHBOARD (LA VERDADERA)
    balance_actual = df['net_profit'].sum()
    df_dep = df[df['magic'] == 0].sort_values('closetime')
    deposito_base = df_dep['net_profit'].iloc[0] if not df_dep.empty else 100000.0
    profit_real_cuenta = balance_actual - deposito_base

    if menu == "🏠 DASHBOARD":
        st.title("⚡ Centro de Mando")
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance Total", f"{balance_actual:,.2f} €")
        c2.metric("Beneficio Real Bots", f"{profit_real_cuenta:,.2f} €")
        c3.metric("Depósito Base", f"{deposito_base:,.2f} €")
        
        st.divider()
        df['equity_total'] = df['net_profit'].cumsum()
        fig = go.Figure(go.Scatter(x=df['closetime'], y=df['equity_total'], mode='lines', line=dict(color='#E1B12C', width=2)))
        fig.update_layout(template="plotly_dark", title="Evolución Histórica de la Cuenta", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    elif menu == "🤖 BOTS":
        st.title("Rendimiento Comparativo de la Flota")
        df_bots = df[df['magic'] != 0].copy()
        
        if df_bots.empty:
            st.info("Sin datos de bots individuales.")
        else:
            listado = sorted([f"BOT {int(m)}" for m in df_bots['magic'].unique()])
            opcion = st.selectbox("Unidad:", ["🔍 VER TODOS"] + listado)
            
            fig_bots = go.Figure()

            if opcion == "🔍 VER TODOS":
                for m in df_bots['magic'].unique():
                    b_df = df_bots[df_bots['magic'] == m].copy()
                    # Forzamos que cada bot empiece en su propia T=0 (primera operación)
                    b_df['profit_cum'] = b_df['net_profit'].cumsum()
                    
                    fig_bots.add_trace(go.Scatter(
                        x=b_df['closetime'], 
                        y=b_df['profit_cum'], 
                        name=f"BOT {int(m)}", 
                        mode='lines'
                    ))
                st.info(f"Rendimiento Neto de la Flota: {df_bots['net_profit'].sum():,.2f} €")
            
            else:
                m_id = int(opcion.replace("BOT ", ""))
                b_df = df_bots[df_bots['magic'] == m_id].copy()
                b_df['profit_cum'] = b_df['net_profit'].cumsum()
                
                # Métricas de la unidad seleccionada
                m1, m2, m3 = st.columns(3)
                m1.metric("Beneficio Acumulado", f"{b_df['net_profit'].sum():,.2f} €")
                m2.metric("Operaciones Realizadas", len(b_df))
                m3.metric("Último Trade", f"{b_df['net_profit'].iloc[-1]:,.2f} €")

                fig_bots.add_trace(go.Scatter(
                    x=b_df['closetime'], 
                    y=b_df['profit_cum'], 
                    name=opcion, 
                    mode='lines+markers', 
                    line=dict(color='#00FFC8', width=3)
                ))

            fig_bots.update_layout(
                template="plotly_dark", 
                height=500,
                xaxis_title="Evolución (Fecha de Cierre)",
                yaxis_title="Beneficio Neto (€)",
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_bots, use_container_width=True)

    elif menu == "📜 HISTORIAL":
        st.title("Grimorio de Operaciones")
        df['label'] = df['magic'].apply(lambda x: "SISTEMA" if x == 0 else f"BOT {int(x)}")
        st.dataframe(
            df[['closetime', 'label', 'symbol', 'net_profit', 'comment']]
            .sort_values('closetime', ascending=False), 
            use_container_width=True,
            hide_index=True
        )

import streamlit as st
import pandas as pd
import joblib
import os
import webbrowser
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# --------- Config ---------
DB_PATH = "data/crypto.db"
FEATURE_PATH = "data/processed/crypto_features.parquet"
MODEL_DIR = "models/"
PRED_LOG_PATH = "data/processed/predictions_log.parquet"
API_URL = "http://127.0.0.1:8000/docs"
AUTO_REFRESH_SEC = 35  # recarregar página a cada N segundos

# --------- Helpers ---------
def _tz_saopaulo(series):
    """Converte séries de datas (string/naive/aware) para timezone America/Sao_Paulo de forma robusta."""
    s = pd.to_datetime(series, utc=True, errors="coerce")
    return s.dt.tz_convert("America/Sao_Paulo")

def _file_info(path):
    if not os.path.exists(path):
        return "arquivo não encontrado"
    t = datetime.fromtimestamp(os.path.getmtime(path))
    return f"{t.strftime('%Y-%m-%d %H:%M:%S')}"

# --------- Cache ---------
@st.cache_data(ttl=30)
def load_features():
    if not os.path.exists(FEATURE_PATH):
        return pd.DataFrame()
    df = pd.read_parquet(FEATURE_PATH)
    df["timestamp"] = _tz_saopaulo(df["timestamp"])
    return df

@st.cache_data(ttl=30)
def load_predictions():
    if not os.path.exists(PRED_LOG_PATH):
        return pd.DataFrame()
    df = pd.read_parquet(PRED_LOG_PATH)

    # renomeia colunas antigas se existirem
    col_map = {
        "symbol": "moeda",
        "timestamp": "horario",
        "predicted_price": "previsao_proxima_hora"
    }
    df = df.rename(columns={c: col_map[c] for c in df.columns if c in col_map})

    # 🔧 força para string antes de converter → evita erro de "duplicate keys"
    df["horario"] = df["horario"].astype(str)
    df["horario"] = pd.to_datetime(df["horario"], utc=True, errors="coerce")

    # timezone → São Paulo
    df["horario"] = df["horario"].dt.tz_convert("America/Sao_Paulo")

    # limpeza e ordenação
    df = df.dropna(subset=["horario", "moeda", "previsao_proxima_hora"]).sort_values("horario")

    return df

# --------- UI Base ---------
st.set_page_config(page_title="Crypto IA Dashboard", layout="wide", page_icon="📊")
st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="refresh")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Previsão de Criptomoedas com IA")

st.markdown(f"""
Este dashboard mostra **preços reais** e **previsões 1h à frente**.

- Atualização automática a cada **{AUTO_REFRESH_SEC}s**
- Modelos **Random Forest** re-treinados em ciclos pelo orquestrador
- Dados locais em **SQLite** / **Parquet**
""")

# 🔗 Botão para abrir API
cols_top = st.columns([1,1,3,3])
with cols_top[0]:
    if st.button("🌐 Acessar API (Swagger UI)"):
        webbrowser.open_new_tab(API_URL)
with cols_top[1]:
    if st.button("🔄 Atualizar agora"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("✅ Cache limpo. Os dados serão recarregados na próxima atualização automática.")

# --------- Load Data ---------
df = load_features()
pred_log = load_predictions()

# Painel de diagnóstico
with st.expander("🛠️ Diagnóstico rápido (arquivos e linhas)"):
    st.write({
        "features_path": FEATURE_PATH,
        "features_modificado_em": _file_info(FEATURE_PATH),
        "features_linhas": 0 if df.empty else len(df),
        "pred_log_path": PRED_LOG_PATH,
        "pred_log_modificado_em": _file_info(PRED_LOG_PATH),
        "pred_log_linhas": 0 if pred_log.empty else len(pred_log),
    })

if df.empty:
    st.warning("Aguardando coleta/processamento... Verifique se o orquestrador está rodando.")
    st.stop()

symbols = df['symbol'].unique()
selected_symbol = st.selectbox("Escolha uma criptomoeda:", symbols)

sub_df = df[df['symbol'] == selected_symbol].sort_values('timestamp')

col1, col2 = st.columns(2)

# ------------------- GRÁFICO DE PREÇOS + PREVISÃO FUTURA -------------------
with col1:
    st.subheader(f"📈 Histórico de Preços - {selected_symbol.upper()}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub_df['timestamp'], y=sub_df['price_usd'],
        mode='lines+markers', name='Preço Real',
        hovertemplate='Tempo: %{x}<br>USD: %{y:.2f}'
    ))
    if not pred_log.empty:
        pl = pred_log[pred_log['moeda'] == selected_symbol].sort_values('horario')
        if not pl.empty:
            fig.add_trace(go.Scatter(
                x=pl['horario'], y=pl['previsao_proxima_hora'],
                mode='lines+markers', name='Previsão 1h à frente',
                line=dict(dash='dash'),
                hovertemplate='Previsto: %{x}<br>USD: %{y:.2f}'
            ))
    fig.update_layout(
        plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
        font=dict(color='white'), xaxis_title="Tempo", yaxis_title="USD"
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ------------------- PREVISÃO (MÉTRICA) -------------------
with col2:
    st.subheader("🤖 Previsão para a próxima hora")
    if pred_log.empty:
        st.info("Nenhuma previsão disponível ainda para esta moeda.")
    else:
        pl = pred_log[pred_log['moeda'] == selected_symbol].sort_values('horario')
        if pl.empty:
            st.info("Nenhuma previsão disponível ainda para esta moeda.")
        else:
            ultima_prev = pl.iloc[-1]
            st.metric(
                "Preço Previsto (1h à frente)",
                f"${ultima_prev['previsao_proxima_hora']:,.2f}",
                help=f"Válido para: {ultima_prev['horario']}"
            )

st.markdown("---")

# ------------------- VARIAÇÃO % -------------------
st.subheader("📊 Variação Percentual entre amostras")
change_fig = go.Figure()
change_fig.add_trace(go.Bar(
    x=sub_df['timestamp'], y=sub_df['price_pct_change_1h'],
    marker_color='orange', name='Variação % por passo',
    hovertemplate='Tempo: %{x}<br>Variação: %{y:.2%}'
))
change_fig.update_layout(
    plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
    font=dict(color='white'), xaxis_title="Tempo", yaxis_title="Variação %"
)
st.plotly_chart(change_fig, use_container_width=True, config={"displayModeBar": False})

# ------------------- EVOLUÇÃO DAS PREVISÕES -------------------
st.subheader("📉 Evolução das Previsões (pontos já recalculados)")
if pred_log.empty:
    st.info("Nenhuma previsão registrada ainda.")
else:
    pl = pred_log[pred_log['moeda'] == selected_symbol].sort_values('horario')
    if pl.empty:
        st.info("Nenhuma previsão registrada para esta moeda.")
    else:
        fig_pred = go.Figure()
        fig_pred.add_trace(go.Scatter(
            x=pl['horario'], y=pl['previsao_proxima_hora'],
            mode='lines+markers', name='Preço Previsto (1h à frente)',
            hovertemplate='Previsto: %{x}<br>USD: %{y:.2f}'
        ))
        fig_pred.update_layout(
            plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
            font=dict(color='white'), xaxis_title="Tempo (futuro)", yaxis_title="Preço Previsto"
        )
        st.plotly_chart(fig_pred, use_container_width=True, config={"displayModeBar": False})

# ------------------- COMPARATIVO ENTRE MOEDAS -------------------
st.markdown("---")
st.subheader("🌍 Comparativo entre Moedas (preço real)")
selected_symbols = st.multiselect("Escolha moedas para comparar:", symbols, default=list(symbols))
fig_compare = go.Figure()
for sym in selected_symbols:
    df_sym = df[df['symbol'] == sym].sort_values('timestamp')
    fig_compare.add_trace(go.Scatter(x=df_sym['timestamp'], y=df_sym['price_usd'], mode='lines', name=sym.upper()))
fig_compare.update_layout(
    plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
    font=dict(color='white'), xaxis_title="Tempo", yaxis_title="USD"
)
st.plotly_chart(fig_compare, use_container_width=True, config={"displayModeBar": False})

# ------------------- EXPORTAÇÃO -------------------
st.markdown("---")
st.subheader("📩 Exportar dados (preço real da moeda selecionada)")
st.download_button(
    label="Baixar CSV",
    data=sub_df.to_csv(index=False).encode('utf-8'),
    file_name=f"{selected_symbol}_historico.csv",
    mime='text/csv'
)

st.caption(f"Atualizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

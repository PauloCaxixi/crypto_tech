# === api/main.py (com validação do arquivo Parquet) ===
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import Response, HTMLResponse
import pandas as pd
import joblib
import os
import numpy as np
from datetime import datetime

FEATURE_PATH = "data/processed/crypto_features.parquet"
MODEL_DIR = "models/"
PRED_LOG_PATH = "data/processed/predictions_log.parquet"

FEATURES = ["price_usd", "price_ma_3", "price_ma_6", "price_pct_change_1h"]

DASHBOARD_URL = "http://127.0.0.1:8501"

app = FastAPI(title="API de Previsão de Criptomoedas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def raiz():
    return {
        "mensagem": "Bem-vindo à API de Previsão de Criptomoedas.",
        "documentacao_swagger": "/docs",
        "documentacao_redoc": "/redoc",
        "status_da_api": "/status",
        "moedas_disponiveis": "/moedas",
        "prever_valor": "/prever/{moeda}",
        "previsoes_registradas": "/previsoes/{moeda}",
        "dashboard": DASHBOARD_URL
    }

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    html = get_swagger_ui_html(openapi_url="/openapi.json", title="API de Previsão de Criptomoedas")
    extra_button = f"""
    <div style='margin:20px;'>
        <a href="{DASHBOARD_URL}" target="_blank">
            <button style="padding:10px; background-color:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer;">
                🌐 Abrir Dashboard
            </button>
        </a>
    </div>
    """
    return HTMLResponse(html.body.decode("utf-8") + extra_button)

@app.get("/redoc", include_in_schema=False)
def redoc_docs():
    html = get_redoc_html(openapi_url="/openapi.json", title="API de Previsão de Criptomoedas")
    extra_button = f"""
    <div style='margin:20px;'>
        <a href="{DASHBOARD_URL}" target="_blank">
            <button style="padding:10px; background-color:#2196F3; color:white; border:none; border-radius:5px; cursor:pointer;">
                📊 Abrir Dashboard
            </button>
        </a>
    </div>
    """
    return HTMLResponse(html.body.decode("utf-8") + extra_button)

# ------------------- FUNÇÕES DE DADOS -------------------

def carregar_dados():
    if not os.path.exists(FEATURE_PATH) or os.path.getsize(FEATURE_PATH) == 0:
        raise HTTPException(status_code=500, detail="Arquivo de features não existe ou está vazio.")

    df = pd.read_parquet(FEATURE_PATH)

    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize("UTC").dt.tz_convert("America/Sao_Paulo")
    else:
        df['timestamp'] = df['timestamp'].dt.tz_convert("America/Sao_Paulo")

    return df

def moedas_disponiveis():
    try:
        df = carregar_dados()
        return sorted(df['symbol'].unique().tolist()) if not df.empty else []
    except:
        return []

@app.get("/status")
def status():
    return {"status": "API online", "horario_atual": datetime.now().isoformat()}

@app.get("/moedas")
def listar_moedas():
    return moedas_disponiveis()

@app.get("/prever/{moeda}")
def prever_valor_futuro(moeda: str = Path(..., description="Escolha uma das moedas disponíveis", examples={"btc": {"summary": "Bitcoin"}}, enum=moedas_disponiveis())):
    df = carregar_dados()
    if df.empty or moeda not in df['symbol'].unique():
        raise HTTPException(status_code=404, detail=f"Moeda '{moeda}' não encontrada ou dados insuficientes.")

    caminho_modelo = os.path.join(MODEL_DIR, f"{moeda}_model.joblib")
    if not os.path.exists(caminho_modelo):
        raise HTTPException(status_code=503, detail="Modelo não treinado para esta moeda.")

    modelo = joblib.load(caminho_modelo)
    mais_recente = df[df['symbol'] == moeda].sort_values('timestamp').iloc[-1]

    features_df = pd.DataFrame([[
        mais_recente['price_usd'],
        mais_recente['price_ma_3'],
        mais_recente['price_ma_6'],
        mais_recente['price_pct_change_1h']
    ]], columns=FEATURES)

    previsao = modelo.predict(features_df)[0]

    registro = {
        "horario": mais_recente['timestamp'].isoformat(),
        "moeda": moeda,
        "preco_atual": mais_recente['price_usd'],
        "previsao_proxima_hora": float(previsao)
    }

    nova_linha = pd.DataFrame([registro])
    if os.path.exists(PRED_LOG_PATH):
        antigo = pd.read_parquet(PRED_LOG_PATH)
        combinado = pd.concat([antigo, nova_linha]).drop_duplicates()
    else:
        combinado = nova_linha
    combinado.to_parquet(PRED_LOG_PATH, index=False)

    return registro

@app.get("/previsoes/{moeda}", summary="Retorna o histórico de previsões")
def historico_previsoes(
    moeda: str = Path(..., description="Escolha uma das moedas disponíveis", examples={"btc": {"summary": "Bitcoin"}}, enum=moedas_disponiveis()),
    inicio: str = Query(None, description="Data e hora inicial no formato YYYY-MM-DDTHH:MM"),
    fim: str = Query(None, description="Data e hora final no formato YYYY-MM-DDTHH:MM"),
    exportar_csv: bool = Query(False, description="Se verdadeiro, retorna os dados como CSV")
):
    if not os.path.exists(PRED_LOG_PATH):
        raise HTTPException(status_code=404, detail="Nenhum log de previsão encontrado.")
    df = pd.read_parquet(PRED_LOG_PATH)
    df = df[df['moeda'] == moeda].sort_values("horario")
    if df.empty:
        raise HTTPException(status_code=404, detail="Nenhum registro encontrado para essa moeda.")

    df['horario'] = pd.to_datetime(df['horario'])

    if inicio:
        df = df[df['horario'] >= pd.to_datetime(inicio)]
    if fim:
        df = df[df['horario'] <= pd.to_datetime(fim)]

    df = df.replace({np.nan: None, np.inf: None, -np.inf: None})

    if exportar_csv:
        return Response(content=df.to_csv(index=False), media_type="text/csv")

    return df.to_dict(orient="records")

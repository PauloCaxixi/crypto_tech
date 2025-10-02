import pandas as pd
import joblib
import os
from datetime import datetime, timedelta
import numpy as np

FEATURE_PATH = "data/processed/crypto_features.parquet"
MODEL_DIR = "models/"
PRED_LOG_PATH = "data/processed/predictions_log.parquet"

FEATURES = ["price_usd", "price_ma_3", "price_ma_6", "price_pct_change_1h"]

def predict(symbol: str):
    if not os.path.exists(FEATURE_PATH):
        print("⚠️ Nenhum dado processado encontrado.")
        return None

    df = pd.read_parquet(FEATURE_PATH)

    # garante que timestamp é datetime com timezone correto
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").dt.tz_convert("America/Sao_Paulo")

    if symbol not in df["symbol"].unique():
        print(f"⚠️ Moeda {symbol.upper()} não encontrada nos dados.")
        return None

    model_path = os.path.join(MODEL_DIR, f"{symbol}_model.joblib")
    if not os.path.exists(model_path):
        print(f"⚠️ Nenhum modelo treinado encontrado para {symbol.upper()}.")
        return None

    modelo = joblib.load(model_path)
    mais_recente = df[df["symbol"] == symbol].sort_values("timestamp").iloc[-1]

    # prepara dataframe com as features esperadas
    features_df = pd.DataFrame([[
        mais_recente["price_usd"],
        mais_recente["price_ma_3"],
        mais_recente["price_ma_6"],
        mais_recente["price_pct_change_1h"]
    ]], columns=FEATURES)

    previsao = modelo.predict(features_df)[0]

    # define timestamp da previsão como 1h à frente do último dado real
    ts_futuro = mais_recente["timestamp"] + timedelta(hours=1)

    registro = {
        "horario": ts_futuro.isoformat(),
        "moeda": symbol,
        "preco_atual": float(mais_recente["price_usd"]),
        "previsao_proxima_hora": float(previsao)
    }

    novo = pd.DataFrame([registro])

    # concatena com histórico anterior, removendo duplicados e valores inválidos
    if os.path.exists(PRED_LOG_PATH):
        antigo = pd.read_parquet(PRED_LOG_PATH)
        combinado = pd.concat([antigo, novo], ignore_index=True)
    else:
        combinado = novo

    # remove duplicatas, NaN e valores infinitos
    combinado = combinado.replace([np.inf, -np.inf], np.nan).dropna()
    combinado = combinado.drop_duplicates(subset=["horario", "moeda"], keep="last")

    # salva no parquet
    combinado.to_parquet(PRED_LOG_PATH, index=False)

    # log no terminal
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Previsão para {symbol.upper()}:")
    print(f"   Preço atual = {mais_recente['price_usd']:.2f}")
    print(f"   Previsão para {ts_futuro.strftime('%d/%m %H:%M')} = {previsao:.2f}\n")

    return registro


if __name__ == "__main__":
    # Testes manuais
    for moeda in ["btc", "eth", "ada", "xrp", "ltc", "sol"]:
        predict(moeda)

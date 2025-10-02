import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from pathlib import Path
from datetime import datetime

FEATURE_PATH = "data/processed/crypto_features.parquet"
MODEL_DIR = "models/"

FEATURES = ["price_usd", "price_ma_3", "price_ma_6", "price_pct_change_1h"]
TARGET = "price_future_1h"

def train_for_symbol(df, symbol):
    df = df[df["symbol"] == symbol].dropna(subset=FEATURES + [TARGET])

    if len(df) < 10:
        print(f"⚠️ Dados insuficientes para treinar {symbol.upper()} (apenas {len(df)} registros). Pulando...")
        return

    X = df[FEATURES]
    y = df[TARGET]

    # Split temporal (sem embaralhar)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = RandomForestRegressor(
        n_estimators=200,  # mais árvores -> mais robustez
        random_state=42,
        n_jobs=-1          # usa todos os núcleos disponíveis
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # 🔎 prints detalhados para debug
    print(f"\n[{datetime.now()}] Modelo treinado para {symbol.upper()}")
    print(f"Registros totais usados: {len(df)}")
    print(f"Período: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"MAE: {mae:.4f}")
    print(f"R² : {r2:.4f}")

    # Salva modelo
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    model_path = f"{MODEL_DIR}/{symbol}_model.joblib"
    joblib.dump(model, model_path)
    print(f"✅ Modelo salvo em {model_path}")

def run():
    if not Path(FEATURE_PATH).exists():
        print(f"⚠️ Arquivo {FEATURE_PATH} não encontrado.")
        return

    df = pd.read_parquet(FEATURE_PATH)

    if df.empty:
        print("⚠️ Nenhum dado encontrado no arquivo de features.")
        return

    print(f"\n[{datetime.now()}] Iniciando treinamento...")
    print(f"Total de registros no dataset: {len(df)}")
    print(f"Moedas disponíveis: {df['symbol'].unique().tolist()}")

    for symbol in df["symbol"].unique():
        train_for_symbol(df, symbol)

if __name__ == "__main__":
    run()

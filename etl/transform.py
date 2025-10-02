import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = "data/crypto.db"
SAVE_PATH = "data/processed/crypto_features.parquet"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM crypto_prices", conn)
    conn.close()

    # força UTC e depois converte p/ São Paulo
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce", utc=True)
    return df

def generate_features(df):
    result = []
    for symbol in df['symbol'].unique():
        sub_df = df[df['symbol'] == symbol].sort_values("timestamp").copy()
        sub_df.set_index("timestamp", inplace=True)

        sub_df["price_ma_3"] = sub_df["price_usd"].rolling(window=3).mean()
        sub_df["price_ma_6"] = sub_df["price_usd"].rolling(window=6).mean()
        sub_df["price_pct_change_1h"] = sub_df["price_usd"].pct_change(periods=1)

        sub_df["price_future_1h"] = sub_df["price_usd"].shift(-1)

        sub_df["symbol"] = symbol
        result.append(sub_df.reset_index())

    full_df = pd.concat(result)

    # ❌ antes: dropna(subset=["price_future_1h"])
    # ✅ agora: só tira linhas que não têm preço_atual
    full_df = full_df.dropna(subset=["price_usd"])

    return full_df

def save_features(df):
    Path("data/processed/").mkdir(parents=True, exist_ok=True)
    df.to_parquet(SAVE_PATH, index=False)

    print(f"[{datetime.now()}] ✅ Features salvas em: {SAVE_PATH}")
    print(f"Total de registros: {len(df)}")
    print(f"Primeira data: {df['timestamp'].min()} | Última data: {df['timestamp'].max()}")

def run():
    df_raw = load_data()
    if df_raw.empty:
        print("⚠️ Nenhum dado encontrado no banco.")
        return
    df_feat = generate_features(df_raw)
    save_features(df_feat)

if __name__ == "__main__":
    run()

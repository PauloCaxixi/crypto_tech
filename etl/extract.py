import requests
import sqlite3
from datetime import datetime

CRYPTOCURRENCIES = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "cardano": "ada",
    "solana": "sol",
    "ripple": "xrp",
    "litecoin": "ltc"
}

DB_PATH = "data/crypto.db"

def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            symbol TEXT,
            price_usd REAL,
            market_cap REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(CRYPTOCURRENCIES.keys()),
        "vs_currencies": "usd",
        "include_market_cap": "true"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[{datetime.now()}] Erro na API: {response.status_code}")
        return None

def save_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for name, values in data.items():
        cursor.execute('''
            INSERT INTO crypto_prices (name, symbol, price_usd, market_cap)
            VALUES (?, ?, ?, ?);
        ''', (
            name,
            CRYPTOCURRENCIES.get(name, ""),
            values.get("usd", 0.0),
            values.get("usd_market_cap", 0.0)
        ))
    conn.commit()
    conn.close()

def run_once():
    print(f"[{datetime.now()}] Iniciando extração única...")
    create_table()
    data = fetch_prices()
    if data:
        save_to_db(data)
        print(f"[{datetime.now()}] Dados salvos com sucesso.")

if __name__ == "__main__":
    run_once()

# 📦 CryptoTech — ETL + ML + API + Dashboard (Tempo Real)

Projeto completo para coletar dados de **criptomoedas** (CoinGecko), armazenar em **SQLite**, processar via **ETL**, treinar **modelos de ML** por moeda, servir previsões via **FastAPI** e visualizar tudo num **dashboard Streamlit** com atualização contínua.

---

## 🏗 Arquitetura

```
[CoinGecko API] → extract.py → (SQLite) → transform.py → features.parquet → train.py → models/
                                                              ↓                      ↓
                                                           FastAPI                 Streamlit
```

---

## ✅ Requisitos

* Python 3.10+ (recomendado 3.12)
* Bibliotecas (instalar com `pip install -r requirements.txt`)

**requirements.txt**

```txt
fastapi
uvicorn
streamlit
requests
pandas
numpy
scikit-learn
joblib
plotly
pyarrow
python-dateutil
```

> **Obs.:** `pyarrow` é necessário para ler/gravar `.parquet`.

---

## ⚙️ Preparação do ambiente

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Pastas necessárias
mkdir data data\processed models
```

---

## ⏱ Orquestração em tempo real (recomendada)

Rodar um **orquestrador separado** que, a cada 30s:

1. coleta uma amostra das moedas; 2) transforma; 3) re-treina modelos (rápido).

### `run_all.py`

```python
import os, time, subprocess, sys

PY = sys.executable  # garante usar o Python do venv
INTERVAL = 30  # segundos

def run(cmd):
    print(f"$ {cmd}")
    return subprocess.call(cmd, shell=True)

def main():
    # loop infinito, coleta UMA VEZ por ciclo (sem travar)
    while True:
        run(f"{PY} etl/extract.py --once")
        run(f"{PY} etl/transform.py")
        run(f"{PY} model/train.py")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
```

> **Por que assim?** O `extract.py` original rodava em loop infinito; isso bloqueava a sequência `transform→train`. Com `--once`, coletamos apenas um snapshot por ciclo, mantendo tudo sincronizado.

### Atualização necessária em `etl/extract.py`

Garanta que **suporta `--once`**:

```python
# acrescente no topo
import argparse

# ... código existente ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Coleta apenas uma vez e sai")
    args = parser.parse_args()

    create_table()
    if args.once:
        data = fetch_prices()
        if data:
            save_to_db(data)
        # encerra
    else:
        # modo contínuo
        print("Iniciando extração contínua...")
        while True:
            data = fetch_prices()
            if data:
                save_to_db(data)
            time.sleep(SLEEP_TIME)
```

> **Dica:** mantenha o `dashboard/app.py` **sem** rodar ETL interno. Deixe o `run_all.py` cuidar disso para evitar processos duplicados.

---

## 🚀 Como rodar (3 terminais separados)

**Terminal 1 — Orquestração:**

```bash
python run_all.py
```

**Terminal 2 — API (FastAPI):**

```bash
uvicorn api.main:app --reload
# Abra: http://127.0.0.1:8000/redoc  (ou /docs)
```

**Terminal 3 — Dashboard (Streamlit):**

```bash
streamlit run dashboard/app.py
```

> O dashboard recarrega dados a cada 30s (cache TTL).

---

## 🔧 Ajustes finos importantes

### 1) Evitar warnings do scikit-learn (feature names)

Ao **prever**, passe um `DataFrame` com as MESMAS colunas usadas no treino:

```python
FEATURES = ["price_usd", "price_ma_3", "price_ma_6", "price_pct_change_1h"]
features_df = pd.DataFrame([[
    mais_recente['price_usd'],
    mais_recente['price_ma_3'],
    mais_recente['price_ma_6'],
    mais_recente['price_pct_change_1h']
]], columns=FEATURES)
previsao = modelo.predict(features_df)[0]
```

Aplique isso em **`api/main.py`** (endpoint `/prever/{moeda}`) e também no **dashboard** na função `predict_price`.

### 2) Timezone correto

Sempre que ler `timestamp` do parquet, aplique:

```python
df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
```

### 3) JSON seguro

Antes de retornar dados históricos:

```python
import numpy as np
df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
```

---

## 🧪 Endpoints principais (todos em PT-BR)

* `GET /` – página inicial amigável com links
* `GET /status` – heartbeat
* `GET /moedas` – lista de moedas disponíveis (símbolos como `btc`, `eth`, `ada`, ...)
* `GET /prever/{moeda}` – previsão da próxima hora para a moeda
* `GET /previsoes/{moeda}?inicio=YYYY-MM-DDTHH:MM&fim=...&exportar_csv=true` – histórico (filtros + CSV)

**Dica:** use `/docs` (Swagger) com **dropdown** de moedas, ou `/redoc` para doc bonita.

---

## 🖥 Dashboard (Resumo)

* Tema escuro, gráficos Plotly
* Histórico de preços, variação %, evolução das **previsões**, e **comparador de moedas**
* Botão de exportar CSV
* Atualiza automaticamente (cache de 30s)

**Melhoria recomendada:** remova a thread que executava ETL dentro do dashboard e deixe apenas:

```python
@st.cache_data(ttl=30)
def load_data():
    # só lê parquet processado
```

> Com o `run_all.py` ativo, o dashboard sempre verá dados frescos.

---

## 🧯 Troubleshooting rápido

* **`NaN` no JSON / erro 500:** já tratado no endpoint (substituição por `null`).
* **Horário diferente no gráfico:** garantir `tz_localize('UTC').tz_convert('America/Sao_Paulo')` no carregamento.
* **`pyarrow` ausente:** instale `pip install pyarrow`.
* **Sem dados suficientes:** deixe o orquestrador rodar alguns minutos.
* **Rate limit CoinGecko:** 10–30 req/min. Mantemos 1 req/30s por ciclo (OK).

---

## 🧾 Roteiro do Vídeo (teaser)

> **Você narrará com os arquivos já rodando.**

1. **Introdução (o que o projeto faz)**: ETL em tempo real, ML por moeda, API e Dashboard.
2. **Arquitetura**: caminhe pela figura e explique cada etapa.
3. **Coleta (extract.py)**: mencione a CoinGecko e o snapshot a cada 30s via `run_all.py`.
4. **ETL (transform.py)**: features (MAs, variação 1h) + label de próxima hora.
5. **ML (train.py)**: RandomForest por moeda; métricas (MAE/R²) no console.
6. **API**: mostre `/redoc`, faça uma chamada `GET /prever/btc` e depois `/previsoes/btc` com filtros.
7. **Dashboard**: histórico, variação, evolução das previsões, comparador, exportar CSV.
8. **Encerramento**: próximos passos (XGBoost/LSTM, deploy, alertas).

> **Na próxima mensagem, te mando um roteiro falado pronto para você ler em voz alta** (com pausas, tempo e ganchos visuais).

---

## 📌 Comandos úteis (Windows PowerShell)

```powershell
# 1) Ativar venv e instalar
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) Orquestrador (terminal 1)
python run_all.py

# 3) API (terminal 2)
uvicorn api.main:app --reload

# 4) Dashboard (terminal 3)
streamlit run dashboard/app.py
```

---

## 📚 Licença

MIT (ou a que preferir).

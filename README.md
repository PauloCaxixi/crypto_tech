📖 README.md

Explicação de como rodar o projeto do zero:

# 🚀 Crypto Forecasting Pipeline

Este projeto implementa um **pipeline de coleta, processamento, treinamento e previsão de preços de criptomoedas**, com visualização em tempo real via **Dashboard (Streamlit)** e uma **API (FastAPI)**.

---

## ⚙️ Estrutura do Projeto



.
├── etl/
│ ├── extract.py # Coleta preços via CoinGecko e salva no SQLite
│ ├── transform.py # Gera features e salva no Parquet
├── model/
│ ├── train.py # Treina modelos RandomForest
│ ├── predict.py # Gera previsões e salva no Parquet
├── api/
│ └── main.py # API FastAPI com endpoints de previsão
├── dashboard/
│ └── app.py # Dashboard Streamlit
├── data/
│ ├── crypto.db # Banco SQLite (criado automaticamente)
│ └── processed/ # Features e previsões em formato Parquet
├── models/ # Modelos treinados (joblib)
├── run_all.py # Orquestrador principal
├── requirements.txt
└── README.md


---

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-repo/crypto-pipeline.git
   cd crypto-pipeline


Crie e ative um ambiente virtual:

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows


Instale as dependências:

pip install -r requirements.txt

▶️ Execução

Rodar tudo (pipeline + API + Dashboard):

python run_all.py


Processo 1 → extract.py coleta preços continuamente

Processo 2 → pipeline transform → train → predict roda a cada 30s

Processo 3 → API FastAPI (porta 8000)

Processo 4 → Dashboard Streamlit (porta 8501)

Processo 5 → abre navegador automaticamente

Acessar:

API → http://127.0.0.1:8000/docs

Dashboard → http://127.0.0.1:8501

📊 Funcionalidades

Coleta de dados em tempo real (CoinGecko API → SQLite).

Geração de features (médias móveis, variação percentual).

Treinamento de modelos Random Forest por moeda.

Previsões automáticas a cada 30s, salvas em parquet.

Dashboard interativo (Streamlit):

Histórico de preços

Previsões futuras

Acurácia das previsões

Comparativo entre moedas

API REST (FastAPI):

/moedas → lista moedas disponíveis

/prever/{moeda} → previsão mais recente

/previsoes/{moeda} → histórico de previsões

📌 Notas

O Dashboard atualiza automaticamente a cada 30s.

A API sempre serve os arquivos mais recentes.

Se quiser mudar a frequência, altere INTERVAL no run_all.py.
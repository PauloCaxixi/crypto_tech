📊 CryptoTech – Previsão de Criptomoedas com IA

Este projeto é um pipeline completo de previsão de preços de criptomoedas utilizando ETL + Machine Learning + API + Dashboard.

Ele coleta preços de criptomoedas em tempo real via CoinGecko, processa os dados, treina modelos de Machine Learning (Random Forest), gera previsões para 1 hora à frente e disponibiliza:

✅ API REST (FastAPI) para consultas

✅ Dashboard interativo (Streamlit) para visualização

✅ Atualizações automáticas a cada 30 segundos

📂 Estrutura do Projeto
crypto_tech/
│── api/
│   └── main.py              # API FastAPI (endpoints de previsão e histórico)
│
│── dashboard/
│   └── app.py               # Dashboard Streamlit
│
│── etl/
│   ├── extract.py           # Coleta preços das criptomoedas (CoinGecko → SQLite)
│   └── transform.py         # Gera features para ML (médias móveis, variação % etc.)
│
│── model/
│   ├── train.py             # Treinamento dos modelos de ML
│   └── predict.py           # Geração de previsões automáticas
│
│── data/
│   ├── crypto.db            # Banco SQLite com preços crus
│   ├── processed/
│   │   ├── crypto_features.parquet   # Features processadas para treino
│   │   └── predictions_log.parquet   # Histórico de previsões
│
│── models/                  # Modelos treinados (um por moeda)
│
│── run_all.py               # Orquestrador (executa ETL + treino + previsão + API + Dashboard)
│── README.md                # Documentação do projeto

⚙️ Requisitos

Python 3.10+

Dependências:

pip install -r requirements.txt


Exemplo de requirements.txt:

fastapi
uvicorn
pandas
scikit-learn
joblib
plotly
streamlit
sqlalchemy
requests
python-multipart

🚀 Como Rodar o Projeto
1️⃣ Rodar tudo de uma vez (recomendado)

O script run_all.py executa todo o pipeline automaticamente:

python run_all.py


Isso vai:

Coletar e atualizar preços (ETL)

Processar features

Treinar os modelos

Gerar previsões

Subir a API (FastAPI) em http://127.0.0.1:8000

Subir o Dashboard (Streamlit) em http://127.0.0.1:8501

2️⃣ Executar manualmente (passo a passo)

Se quiser rodar cada parte separadamente:

🔹 Coletar dados (ETL – Extract)
python etl/extract.py


👉 Salva preços em tempo real no data/crypto.db.

🔹 Processar dados (ETL – Transform)
python etl/transform.py


👉 Gera features (médias móveis, variação percentual etc.) em data/processed/crypto_features.parquet.

🔹 Treinar modelos
python model/train.py


👉 Cria/atualiza modelos Random Forest para cada moeda em models/.

🔹 Gerar previsões
python model/predict.py


👉 Calcula a previsão para 1h à frente e salva no predictions_log.parquet.

🔹 Subir API
uvicorn api.main:app --reload --port 8000


👉 Documentação Swagger: http://127.0.0.1:8000/docs
👉 Documentação Redoc: http://127.0.0.1:8000/redoc

🔹 Subir Dashboard
streamlit run dashboard/app.py --server.port 8501


👉 Acesse em: http://127.0.0.1:8501

📡 API – Endpoints disponíveis
🔹 Raiz
GET /


Retorna informações gerais da API.

🔹 Status
GET /status


Retorna status atual da API.

🔹 Listar moedas disponíveis
GET /moedas

🔹 Prever valor futuro
GET /prever/{moeda}


Exemplo:

http://127.0.0.1:8000/prever/btc

🔹 Histórico de previsões
GET /previsoes/{moeda}


Parâmetros opcionais:

inicio: Data inicial (YYYY-MM-DDTHH:MM)

fim: Data final (YYYY-MM-DDTHH:MM)

exportar_csv: true para exportar CSV

📊 Dashboard – Funcionalidades

O Dashboard em Streamlit permite:

📈 Visualizar histórico de preços

🤖 Ver previsões de 1h à frente

📉 Acompanhar evolução das previsões no tempo

📊 Monitorar variação percentual dos preços

🌍 Comparar diferentes moedas

🎯 Ver acurácia das previsões (erro absoluto e percentual)

📩 Exportar dados em CSV

🔗 Botão para acessar API diretamente

🔮 Modelagem (Machine Learning)

Modelo: Random Forest Regressor

Features utilizadas:

price_usd – preço atual

price_ma_3 – média móvel de 3 períodos

price_ma_6 – média móvel de 6 períodos

price_pct_change_1h – variação percentual em 1h

Target: price_future_1h – preço real da próxima hora

O modelo é re-treinado constantemente a cada ciclo do pipeline.

📌 Exemplo de fluxo

extract.py coleta preços atuais de BTC e ETH.

transform.py calcula médias móveis e variação percentual.

train.py treina um modelo Random Forest para cada moeda.

predict.py prevê o preço 1h à frente e salva em log.

O dashboard exibe preços reais, previsões e erros.

A API permite consultar valores e previsões externamente.

🧑‍💻 Autor

Projeto desenvolvido como um sistema completo de previsão de criptomoedas com IA para aprendizado, integração de ETL, Machine Learning e visualização interativa.
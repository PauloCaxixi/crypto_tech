# run_all.py
import os
import time
import subprocess
import sys
import multiprocessing
import webbrowser
from pathlib import Path

PY = sys.executable
INTERVAL = 30  # segundos entre ciclos ETL + treino + predição
API_URL = "http://127.0.0.1:8000/docs"
DASHBOARD_URL = "http://127.0.0.1:8501"

def run(cmd):
    print(f"\n$ {cmd}")
    return subprocess.call(cmd, shell=True)

def etl_loop():
    """Loop contínuo: extrai, transforma, treina e prevê"""
    while True:
        run(f"{PY} etl/extract.py --once")
        run(f"{PY} etl/transform.py")
        run(f"{PY} model/train.py")
        run(f"{PY} model/predict.py")  # 🔮 gera previsões para todas as moedas
        print(f"✅ ciclo concluído — aguardando {INTERVAL}s...\n")
        time.sleep(INTERVAL)

def start_api():
    run(f"{PY} -m uvicorn api.main:app --reload --port 8000")

def start_dashboard():
    run(f"{PY} -m streamlit run dashboard/app.py --server.port 8501 --server.headless true")

def open_browser():
    # espera alguns segundos para API/Dashboard subirem
    webbrowser.open_new_tab(DASHBOARD_URL)
    time.sleep(3)
    webbrowser.open_new_tab(API_URL)

def main():
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(parents=True, exist_ok=True)

    # cria processos independentes
    p1 = multiprocessing.Process(target=etl_loop)
    p2 = multiprocessing.Process(target=start_api)
    p3 = multiprocessing.Process(target=start_dashboard)
    p4 = multiprocessing.Process(target=open_browser)

    # inicia todos
    p1.start()
    p2.start()
    p3.start()
    p4.start()

    # mantém vivos
    p1.join()
    p2.join()
    p3.join()
    p4.join()

if __name__ == "__main__":
    main()

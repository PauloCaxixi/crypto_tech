# run_all.py
import os
import time
import subprocess
import sys
import multiprocessing
import webbrowser
from pathlib import Path

PY = sys.executable
INTERVAL = 30  # segundos
API_URL = "http://127.0.0.1:8000/docs"
DASHBOARD_URL = "http://127.0.0.1:8501"

def run(cmd):
    """Executa comando no terminal"""
    print(f"\n$ {cmd}")
    return subprocess.call(cmd, shell=True)

# ---------- Processos ----------
def start_extractor():
    """Roda o coletor contínuo de preços (CoinGecko → SQLite)"""
    run(f"{PY} etl/extract.py")

def pipeline_loop():
    """Loop contínuo de transform → train → predict"""
    while True:
        try:
            run(f"{PY} etl/transform.py")
            run(f"{PY} model/train.py")
            run(f"{PY} model/predict.py")
            print(f"✅ Ciclo concluído — aguardando {INTERVAL}s...\n")
        except Exception as e:
            print(f"❌ Erro no ciclo: {e}")
        time.sleep(INTERVAL)

def start_api():
    """Sobe API FastAPI"""
    run(f"{PY} -m uvicorn api.main:app --reload")

def start_dashboard():
    """Sobe Dashboard Streamlit"""
    run(f"{PY} -m streamlit run dashboard/app.py")

def open_browser():
    """Abre API e Dashboard no navegador"""
    webbrowser.open_new_tab(DASHBOARD_URL)
    time.sleep(5)  # espera serviços subirem
    webbrowser.open_new_tab(API_URL)


# ---------- Orquestrador ----------
def main():
    # garante pastas necessárias
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(parents=True, exist_ok=True)

    # cria processos independentes
    p1 = multiprocessing.Process(target=start_extractor)
    p2 = multiprocessing.Process(target=pipeline_loop)
    p3 = multiprocessing.Process(target=start_api)
    p4 = multiprocessing.Process(target=start_dashboard)
    p5 = multiprocessing.Process(target=open_browser)

    # inicia todos
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()

    # mantém vivos
    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()

if __name__ == "__main__":
    main()

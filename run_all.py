# run_all.py
import os
import time
import subprocess
import sys
import multiprocessing
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DASHBOARD = PROJECT_ROOT / "dashboard" / "app.py"
PY = sys.executable

INTERVAL = 30  # segundos entre ciclos do ETL
API_URL = "http://127.0.0.1:8000/docs"
DASHBOARD_URL = "http://127.0.0.1:8501"

def run(cmd, cwd=None):
    """Executa comando em subprocess não-bloqueante"""
    print(f"\n$ {' '.join(cmd)} (cwd={cwd or os.getcwd()})")
    return subprocess.Popen(cmd, cwd=cwd, shell=False)

def etl_loop():
    while True:
        subprocess.call([PY, "etl/extract.py", "--once"])
        subprocess.call([PY, "etl/transform.py"])
        subprocess.call([PY, "model/train.py"])
        subprocess.call([PY, "model/predict.py"])
        print(f"✅ Ciclo ETL concluído — aguardando {INTERVAL}s...\n")
        time.sleep(INTERVAL)

def start_api():
    run([PY, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=str(PROJECT_ROOT))

def start_dashboard():
    run([
        PY, "-m", "streamlit", "run", str(DASHBOARD),
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ], cwd=str(PROJECT_ROOT))

def open_browser():
    time.sleep(8)  # espera API e Dashboard subirem
    webbrowser.open_new_tab(DASHBOARD_URL)
    webbrowser.open_new_tab(API_URL)

def main():
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(parents=True, exist_ok=True)

    p1 = multiprocessing.Process(target=etl_loop)
    p2 = multiprocessing.Process(target=start_api)
    p3 = multiprocessing.Process(target=start_dashboard)
    p4 = multiprocessing.Process(target=open_browser)

    p1.start()
    p2.start()
    p3.start()
    p4.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()

if __name__ == "__main__":
    main()

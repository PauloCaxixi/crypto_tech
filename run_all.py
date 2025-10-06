# === run_all.py ===
import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
import webbrowser

PROJECT_ROOT = Path(__file__).resolve().parent
PY = sys.executable

EXTRACT = PROJECT_ROOT / "etl" / "extract.py"
TRANSFORM = PROJECT_ROOT / "etl" / "transform.py"
TRAIN = PROJECT_ROOT / "model" / "train.py"
PREDICT = PROJECT_ROOT / "model" / "predict.py"

FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "crypto_features.parquet"
PRED_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "predictions_log.parquet"

API_HOST = "127.0.0.1"
API_PORT = "8000"
DASH_PORT = "8501"

API_URL = f"http://{API_HOST}:{API_PORT}/docs"
DASHBOARD_URL = f"http://127.0.0.1:{DASH_PORT}"

CYCLE_SECONDS = 30
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / f"run_all_{datetime.now().strftime('%Y%m%d')}.log"

def setup_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n=== Início da execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{ts}] {msg}"
    print(full_msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def run_step(name: str, cmd: list[str]) -> bool:
    log(f"➡️  {name}: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True
    )
    for line in process.stdout:
        print(f"   {line}", end="")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("   " + line)
    process.wait()
    if process.returncode == 0:
        log(f"✅ {name} concluído com sucesso.")
        return True
    else:
        log(f"❌ {name} falhou (exit={process.returncode}).")
        return False

def ts_file(path: Path) -> str:
    if not path.exists():
        return "—"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

def start_api():
    log("🌐 Iniciando API (Uvicorn)...")
    subprocess.Popen(
        [PY, "-m", "uvicorn", "api.main:app", "--host", API_HOST, "--port", API_PORT],
        cwd=str(PROJECT_ROOT),
        shell=True
    )

def start_dashboard():
    log("📊 Iniciando Dashboard (Streamlit)...")
    subprocess.Popen(
        [PY, "-m", "streamlit", "run", str(PROJECT_ROOT / "dashboard" / "app.py"),
         "--server.port", str(DASH_PORT),
         "--server.headless", "true"],
        cwd=str(PROJECT_ROOT),
        shell=True
    )

def open_browser():
    time.sleep(8)
    log("🌍 Abrindo navegador (Dashboard + API)...")
    webbrowser.open_new_tab(DASHBOARD_URL)
    webbrowser.open_new_tab(API_URL)

def etl_loop():
    while True:
        log("🚀 Iniciando ciclo ETL (Extract → Transform → Train → Predict)...")

        if not run_step("Extract", [PY, str(EXTRACT)]):
            time.sleep(CYCLE_SECONDS); continue

        if not run_step("Transform", [PY, str(TRANSFORM)]):
            time.sleep(CYCLE_SECONDS); continue
        log(f"📦 Features atualizadas: {ts_file(FEATURES_PATH)}")

        if not run_step("Train", [PY, str(TRAIN)]):
            time.sleep(CYCLE_SECONDS); continue

        if not run_step("Predict", [PY, str(PREDICT)]):
            time.sleep(CYCLE_SECONDS); continue
        log(f"📝 Log de previsões atualizado: {ts_file(PRED_LOG_PATH)}")

        log(f"✅ Ciclo ETL concluído. Próxima execução em {CYCLE_SECONDS}s...\n")
        time.sleep(CYCLE_SECONDS)

def main():
    setup_logger()
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "models").mkdir(parents=True, exist_ok=True)

    log("🧠 Orquestrador iniciado.")

    threading.Thread(target=start_api, daemon=True).start()
    threading.Thread(target=start_dashboard, daemon=True).start()
    threading.Thread(target=open_browser, daemon=True).start()

    etl_loop()

if __name__ == "__main__":
    main()
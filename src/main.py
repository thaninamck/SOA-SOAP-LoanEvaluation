import os
import subprocess
import time
import signal
import sys

# --- CONFIG --- #
SERVICES = [
    ("Information Extraction", "services/information_extraction.py", 8001),
    ("Credit Check", "services/credit_check.py", 8002),
    ("Property Evaluation", "services/property_evaluation.py", 8003),
    ("Decision Service", "services/decision_service.py", 8004),
    ("Composite Service", "composite_service/service_composite.py", 8000),
]

PYTHON = sys.executable  # uses current environment's Python
PROCESSES = []


def run_service(name, script, port):
    """Start one service as a detached subprocess."""
    print(f"🚀 Starting {name} on port {port}...")
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name.replace(' ', '_').lower()}.log")

    with open(log_file, "w", encoding="utf-8") as f:
        # Start without piping stdout/stderr to prevent blocking
        proc = subprocess.Popen(
            [PYTHON, script],
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        )

    PROCESSES.append((name, proc))
    time.sleep(1)

    if proc.poll() is None:
        print(f"✅ {name} running (PID: {proc.pid}) → logs in {log_file}")
    else:
        print(f"❌ Failed to start {name}")
    return proc


def start_all():
    """Launch all services sequentially."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_path)

    for name, script, port in SERVICES:
        script_path = os.path.join(base_path, script)
        if not os.path.exists(script_path):
            print(f"⚠️ Warning: script not found -> {script_path}")
            continue
        run_service(name, script_path, port)
        time.sleep(2)

    print("\n🌐 All services started successfully!\n")
    print("🧩 Composite service is available at:")
    print("   👉 http://127.0.0.1:8000/LoanEvaluationService?wsdl\n")


def stop_all():
    """Gracefully stop all running services."""
    print("\n🛑 Stopping all services...")
    for name, proc in PROCESSES:
        if proc.poll() is None:
            print(f"Terminating {name} (PID: {proc.pid})...")
            try:
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print(f"Force killing {name}")
                proc.kill()
    print("✅ All services stopped.")


if __name__ == "__main__":
    try:
        start_all()
        print("🔄 Press Ctrl+C to stop all services.\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        stop_all()

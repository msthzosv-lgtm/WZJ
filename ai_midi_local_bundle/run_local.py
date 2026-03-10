from __future__ import annotations

import importlib
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ensure_deps() -> None:
    required = ["fastapi", "uvicorn", "librosa", "pretty_midi"]
    missing = []
    for mod in required:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)

    if missing:
        raise RuntimeError(
            "缺少依赖: " + ", ".join(missing) + "。请先执行 pip install -r backend/requirements.txt"
        )


def main() -> int:
    ensure_deps()

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8780",
    ]
    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        "8088",
        "--directory",
        str(ROOT / "frontend"),
    ]

    backend = subprocess.Popen(backend_cmd, cwd=ROOT)
    frontend = subprocess.Popen(frontend_cmd, cwd=ROOT)
    print("Backend: http://127.0.0.1:8780")
    print("Frontend: http://127.0.0.1:8088")

    time.sleep(1.8)
    webbrowser.open("http://127.0.0.1:8088")

    try:
        while True:
            if backend.poll() is not None:
                print("Backend exited.")
                break
            if frontend.poll() is not None:
                print("Frontend exited.")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                proc.terminate()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

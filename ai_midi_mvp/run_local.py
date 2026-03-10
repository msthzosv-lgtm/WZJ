from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8765",
    ]
    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        "8080",
        "--directory",
        str(ROOT / "frontend"),
    ]

    backend = subprocess.Popen(backend_cmd, cwd=ROOT)
    frontend = subprocess.Popen(frontend_cmd, cwd=ROOT)
    print("Backend: http://127.0.0.1:8765")
    print("Frontend: http://127.0.0.1:8080")

    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8080")

    try:
        while True:
            if backend.poll() is not None or frontend.poll() is not None:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in (backend, frontend):
            if p.poll() is None:
                p.terminate()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

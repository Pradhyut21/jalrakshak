"""Portable local launcher. --setup installs locked dependencies and builds the UI."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser
from threading import Timer

ROOT = Path(__file__).resolve().parent.parent


def command(args, cwd=ROOT, env=None):
    subprocess.run([str(value) for value in args], cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if args.setup:
        if sys.version_info < (3, 13):
            raise SystemExit("Use Python 3.13 or newer to create the virtual environment.")
        if not python.exists():
            command([sys.executable, "-m", "venv", ROOT / ".venv"])
        lock = ROOT / "backend/requirements-lock.txt"
        command([python, "-m", "pip", "install", "-r", lock])
        npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
        if not npm:
            raise SystemExit("Install Node.js 22.18+ (or a newer supported LTS) including npm, then rerun --setup.")
        command([npm, "ci"], ROOT / "frontend")
        command([npm, "run", "build"], ROOT / "frontend")
    if not python.exists():
        raise SystemExit("First run: python scripts/run.py --setup")
    if not (ROOT / "frontend/dist/index.html").exists():
        raise SystemExit("The interface must be built first: python scripts/run.py --setup")
    url = f"http://127.0.0.1:{args.port}"
    env = os.environ.copy()
    origins = env.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    origins.extend([url, f"http://localhost:{args.port}"])
    env["ALLOWED_ORIGINS"] = ",".join(dict.fromkeys(origin.strip() for origin in origins if origin.strip()))
    print(f"JalRakshak simulated demo: {url}\nPress Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        Timer(2.0, lambda: webbrowser.open(url)).start()
    try:
        command([python, "-m", "uvicorn", "app.main:app", "--app-dir", ROOT / "backend", "--host", "127.0.0.1", "--port", args.port], env=env)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

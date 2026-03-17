#!/usr/bin/env python3
"""
JARVIS4 AI OFFICE — Launch Script

Opens the visual office dashboard in the browser
and starts the backend server in the background.

This does NOT interfere with cloud operations —
the dashboard is a read-only monitoring interface
that connects via WebSocket/API.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
OFFICE_HTML = PROJECT_DIR / "frontend" / "office.html"
RUN_SCRIPT = PROJECT_DIR / "run.py"


def main():
    print("=" * 50)
    print("  🏢 JARVIS4 AI OFFICE — Запуск")
    print("=" * 50)

    # 1. Open the office dashboard in browser
    print("\n[1] Открываю визуальный офис...")
    office_url = OFFICE_HTML.as_uri()
    webbrowser.open(office_url)
    print(f"    → {office_url}")

    # 2. Start backend server in background
    print("\n[2] Запускаю бэкенд сервер...")
    try:
        # Start run.py as a background process
        if sys.platform == "win32":
            proc = subprocess.Popen(
                [sys.executable, str(RUN_SCRIPT)],
                cwd=str(PROJECT_DIR),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, str(RUN_SCRIPT)],
                cwd=str(PROJECT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        print(f"    → Сервер запущен (PID: {proc.pid})")
    except Exception as e:
        print(f"    ⚠ Не удалось запустить сервер: {e}")
        print("    → Офис работает в автономном режиме")

    print("\n" + "=" * 50)
    print("  ✅ Офис Jarvis4 открыт!")
    print("  📡 Дашборд подключится к серверу автоматически")
    print("  🌐 Облачная работа агентов не прерывается")
    print("=" * 50)


if __name__ == "__main__":
    main()

@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo RAT is not installed. Running installer...
    call install_rat.bat
)

call venv\Scripts\activate.bat
start "" pythonw main.py

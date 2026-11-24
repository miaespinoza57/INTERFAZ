@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Primero abre instalar.bat
    pause
    exit /b 1
)
rem Sin argumentos usa simulacion. Con el Arduino: jugar.bat --serial --port COM6
.venv\Scripts\python main.py %*
if errorlevel 1 pause

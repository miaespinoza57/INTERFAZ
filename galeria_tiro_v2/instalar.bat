@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Instalando la Galeria de Tiro Laser...
where py >nul 2>nul
if errorlevel 1 (
    echo.
    echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
    echo y marca la casilla "Add python.exe to PATH" en el instalador.
    pause
    exit /b 1
)
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Hubo un error al instalar. Revisa tu conexion a internet.
    pause
    exit /b 1
)
echo.
echo Listo. Ahora abre jugar.bat
pause

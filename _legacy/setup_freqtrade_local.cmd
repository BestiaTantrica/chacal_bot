@echo off
REM ==================================================
REM PROTOCOLO CHACAL - SETUP FREQTRADE LOCAL
REM ==================================================

echo.
echo ====================================
echo  INSTALANDO FREQTRADE LOCAL
echo ====================================
echo.

REM Crear entorno virtual si no existe
if not exist ".venv\" (
    echo [1/3] Creando entorno virtual...
    python -m venv .venv
)

echo [2/3] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo [3/3] Instalando Freqtrade...
python -m pip install --upgrade pip
pip install freqtrade

echo.
echo ====================================
echo  INSTALACION COMPLETADA
echo ====================================
echo.
echo Para activar el entorno:
echo  .venv\Scripts\activate.bat
echo.
pause

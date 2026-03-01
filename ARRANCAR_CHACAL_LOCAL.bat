@echo off
TITLE CHACAL V4 - MODO CENTINELA (LONDRES)
echo ======================================================
echo          CHACAL V4 - OPERACION LONDRES 
echo ======================================================

:: Asegurar que estamos en el directorio del script
cd /d "%~dp0"

echo "[1/3] Verificando Docker..."
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo "[ERROR] Docker no esta instalado o no esta en el PATH."
    echo "Asegurate de tener Docker Desktop abierto."
    pause
    exit /b
)

echo "[2/3] Verificando Configuracion..."
if not exist "LIVE_STAGING\config_chacal_v4_live.json" (
    echo "[ERROR] No se encontro el archivo de config en LIVE_STAGING."
    pause
    exit /b
)

echo "[3/3] Lanzando Chacal V4..."
echo "[INFO] El bot estara en espera hasta las Horas Magicas (04:55 AR)."
echo "[INFO] Presiona Ctrl+C para detener."
echo "------------------------------------------------------"

docker run --rm -it --name chacal_londres_local ^
  -v "%cd%\user_data:/freqtrade/user_data" ^
  -v "%cd%\LIVE_STAGING:/freqtrade/LIVE_STAGING" ^
  freqtradeorg/freqtrade:develop ^
  trade --config LIVE_STAGING/config_chacal_v4_live.json --strategy ChacalPulseV4_Hyperopt

echo ------------------------------------------------------
echo [FIN] El proceso se ha detenido.
pause

@echo off
REM ==================================================
REM PROTOCOLO CHACAL - DOWNLOAD DATA (DOCKER)
REM ==================================================

echo.
echo ====================================
echo  DESCARGANDO DATOS - CHACAL
echo ====================================
echo.

docker run --rm ^
  -v "%cd%/user_data:/freqtrade/user_data" ^
  --workdir /freqtrade ^
  freqtradeorg/freqtrade:stable ^
  download-data ^
  --config user_data/config_chacal_aws.json ^
  --timeframe 5m ^
  --days 60

echo.
echo ====================================
echo  DESCARGA COMPLETADA
echo ====================================
echo.
pause

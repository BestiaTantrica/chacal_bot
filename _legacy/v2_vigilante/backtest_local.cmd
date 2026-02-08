@echo off
REM ==================================================
REM PROTOCOLO CHACAL - BACKTEST LOCAL (DOCKER)
REM ==================================================

echo.
echo ====================================
echo  BACKTEST CHACAL - DOCKER
echo ====================================
echo.

REM Ejecutar backtest usando Docker
REM Nota: Usar path absoluto de Windows convertido a formato Docker

docker run --rm ^
  -v "%cd%/user_data:/freqtrade/user_data" ^
  --workdir /freqtrade ^
  freqtradeorg/freqtrade:stable ^
  backtesting ^
  --config user_data/config_backtest.json ^
  --strategy EstrategiaChacal ^
  --timeframe 5m


echo.
echo ====================================
echo  BACKTEST COMPLETADO
echo ====================================
echo.
pause

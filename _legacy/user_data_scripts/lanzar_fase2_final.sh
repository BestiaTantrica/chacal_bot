#!/bin/bash
# SCRIPT MAESTRO FASE 2 - VERSIÓN FINAL CORREGIDA
# Ejecuta Hyperopt 5m para 12 monedas en 4 torres secuenciales

cd /home/ec2-user/chacal_bot

echo "$(date '+%Y-%m-%d %H:%M:%S') - [INICIO] Fase 2 Final" | tee -a user_data/logs/fase2_final.log

# 1. LIMPIEZA
echo "$(date '+%Y-%m-%d %H:%M:%S') - [LIMPIEZA] Deteniendo contenedores..." | tee -a user_data/logs/fase2_final.log
docker rm -f $(docker ps -aq) 2>/dev/null

# 2. DESCARGA DE DATOS (365 días, 5m, sintaxis CORRECTA para Futures)
echo "$(date '+%Y-%m-%d %H:%M:%S') - [DESCARGA] Iniciando (12 pares, 365 días)..." | tee -a user_data/logs/fase2_final.log
docker run --rm \
  -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop \
  download-data \
  --config user_data/config_download.json \
  --timeframe 5m \
  --days 365 \
  --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT BNB/USDT:USDT XRP/USDT:USDT ADA/USDT:USDT DOGE/USDT:USDT AVAX/USDT:USDT LINK/USDT:USDT DOT/USDT:USDT SUI/USDT:USDT NEAR/USDT:USDT \
  2>&1 | tee -a user_data/logs/fase2_final.log

echo "$(date '+%Y-%m-%d %H:%M:%S') - [DESCARGA] Completada" | tee -a user_data/logs/fase2_final.log

# 3. PODA DE DATOS (solo Horas Mágicas, sintaxis CORRECTA)
echo "$(date '+%Y-%m-%d %H:%M:%S') - [PODA] Iniciando reducción 80%..." | tee -a user_data/logs/fase2_final.log
docker run --rm \
  -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data \
  --entrypoint python3 \
  freqtradeorg/freqtrade:develop \
  /freqtrade/user_data/podar_datos_5m.py \
  2>&1 | tee -a user_data/logs/fase2_final.log

echo "$(date '+%Y-%m-%d %H:%M:%S') - [PODA] Completada" | tee -a user_data/logs/fase2_final.log

# 4. TORRE ALPHA (BTC, ETH, SOL)
echo "$(date '+%Y-%m-%d %H:%M:%S') - [ALPHA] Iniciando..." | tee -a user_data/logs/fase2_final.log
./user_data/cola_hyperopt_5m_alpha.sh 2>&1 | tee -a user_data/logs/fase2_final.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - [ALPHA] Completada" | tee -a user_data/logs/fase2_final.log

# 5. TORRE BETA (BNB, XRP, ADA)
echo "$(date '+%Y-%m-%d %H:%M:%S') - [BETA] Iniciando..." | tee -a user_data/logs/fase2_final.log
./user_data/cola_hyperopt_5m_beta.sh 2>&1 | tee -a user_data/logs/fase2_final.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - [BETA] Completada" | tee -a user_data/logs/fase2_final.log

# 6. TORRE GAMMA (DOGE, AVAX, LINK)
echo "$(date '+%Y-%m-%d %H:%M:%S') - [GAMMA] Iniciando..." | tee -a user_data/logs/fase2_final.log
./user_data/cola_hyperopt_5m_gamma.sh 2>&1 | tee -a user_data/logs/fase2_final.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - [GAMMA] Completada" | tee -a user_data/logs/fase2_final.log

# 7. TORRE DELTA (DOT, SUI, NEAR)
echo "$(date '+%Y-%m-%d %H:%M:%S') - [DELTA] Iniciando..." | tee -a user_data/logs/fase2_final.log
./user_data/cola_hyperopt_5m_delta.sh 2>&1 | tee -a user_data/logs/fase2_final.log
echo "$(date '+%Y-%m-%d %H:%M:%S') - [DELTA] Completada" | tee -a user_data/logs/fase2_final.log

echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ MISION CUMPLIDA - FASE 2 FINALIZADA" | tee -a user_data/logs/fase2_final.log

#!/bin/bash
# Script para extraer parámetros de las 12 monedas desde archivos .fthypt

MONEDAS=(
  "BTC:strategy_ChacalPulseV4_Hyperopt_2026-02-08_04-13-46.fthypt"
  "ETH:strategy_ChacalPulseV4_Hyperopt_2026-02-08_05-37-25.fthypt"
  "SOL:strategy_ChacalPulseV4_Hyperopt_2026-02-08_07-10-36.fthypt"
  "BNB:strategy_ChacalPulseV4_Hyperopt_2026-02-08_08-13-56.fthypt"
  "XRP:strategy_ChacalPulseV4_Hyperopt_2026-02-08_11-12-53.fthypt"
  "ADA:strategy_ChacalPulseV4_Hyperopt_2026-02-08_12-02-13.fthypt"
  "DOGE:strategy_ChacalPulseV4_Hyperopt_2026-02-08_15-44-20.fthypt"
  "AVAX:strategy_ChacalPulseV4_Hyperopt_2026-02-08_16-27-42.fthypt"
  "LINK:strategy_ChacalPulseV4_Hyperopt_2026-02-08_18-13-01.fthypt"
  "DOT:strategy_ChacalPulseV4_Hyperopt_2026-02-08_19-39-48.fthypt"
  "SUI:strategy_ChacalPulseV4_Hyperopt_2026-02-08_21-24-46.fthypt"
  "NEAR:strategy_ChacalPulseV4_Hyperopt_2026-02-08_23-03-35.fthypt"
)

cd /home/ec2-user/chacal_bot

for ENTRY in "${MONEDAS[@]}"; do
  MONEDA="${ENTRY%%:*}"
  FILE="${ENTRY##*:}"
  
  echo "=== Extrayendo $MONEDA de $FILE ==="
  
  docker run --rm \
    -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data \
    freqtradeorg/freqtrade:develop \
    hyperopt-show -n -1 \
    --hyperopt-filename "$FILE" \
    --no-header \
    --print-json > "user_data/hyperopt_results/fase2_${MONEDA}.json"
  
  echo "Guardado en user_data/hyperopt_results/fase2_${MONEDA}.json"
done

echo "✅ Extracción completada"

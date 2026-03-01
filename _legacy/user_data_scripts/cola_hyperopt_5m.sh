#!/bin/bash
# Cola de Hyperopt Fase 2: Refinamiento de Francotirador (5m)
# Protocolo Chacal: 12 meses, 1000 epocas, Horas Mágicas.

COINS=("BTC/USDT:USDT" "ETH/USDT:USDT" "SOL/USDT:USDT" "XRP/USDT:USDT" "ADA/USDT:USDT" "DOT/USDT:USDT" "DOGE/USDT:USDT" "AVAX/USDT:USDT" "LINK/USDT:USDT" "BNB/USDT:USDT" "SUI/USDT:USDT" "NEAR/USDT:USDT")

for PAIR in "${COINS[@]}"; do
    NAME=$(echo $PAIR | cut -d'/' -f1)
    echo "=========================================="
    echo "INICIANDO HYPEROPT 5m (REFINADO) PARA: $NAME"
    echo "=========================================="
    
    # Timerange: 20250101- equivale a ~13-14 meses desde la fecha actual (Feb 2026).
    # Ajustado para tener margen de sobra.
    
    sudo docker-compose -f docker-compose_relevo.yml run --rm --name "hyperopt_5m_$NAME" chacal_alpha hyperopt \
        --config user_data/config_alpha.json \
        --strategy ChacalPulseV4_Hyperopt \
        --hyperopt-loss SharpeHyperOptLoss \
        --spaces buy sell \
        --timeframe 5m \
        --timerange 20250101- \
        --pairs "$PAIR" \
        --epochs 1000 \
        -j 1 \
        --data-format-ohlcv feather \
        --userdir user_data
    
    echo "FINALIZADO REFINADO: $NAME"
    echo "------------------------------------------"
done

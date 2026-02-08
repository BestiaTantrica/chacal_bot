#!/bin/bash
# Cola de Optimización Quirúrgica - Batallón Elite (12 Unidades)
# Este script procesa una moneda a la vez para proteger la RAM de la t2.micro.

COINS=("BTC/USDT:USDT" "ETH/USDT:USDT" "SOL/USDT:USDT" "XRP/USDT:USDT" "ADA/USDT:USDT" "DOT/USDT:USDT" "DOGE/USDT:USDT" "AVAX/USDT:USDT" "LINK/USDT:USDT" "BNB/USDT:USDT" "SUI/USDT:USDT" "NEAR/USDT:USDT")

for PAIR in "${COINS[@]}"; do
    NAME=$(echo $PAIR | cut -d'/' -f1)
    echo "=========================================="
    echo "INICIANDO HYPEROPT PARA: $NAME"
    echo "=========================================="
    
    sudo docker-compose -f docker-compose_relevo.yml run --rm --name "hyperopt_$NAME" chacal_alpha hyperopt \
        --config user_data/config_alpha.json \
        --strategy ChacalPulseV4_Hyperopt \
        --hyperopt-loss SharpeHyperOptLoss \
        --spaces buy sell \
        --timeframe 1m \
        --timerange 20251101- \
        --pairs "$PAIR" \
        --epochs 500 \
        -j 1 \
        --data-format-ohlcv feather \
        --userdir user_data
    
    echo "FINALIZADO: $NAME"
    echo "------------------------------------------"
done

#!/bin/bash
# Torre Alpha: BTC, ETH, SOL
PAIRS=("BTC/USDT:USDT" "ETH/USDT:USDT" "SOL/USDT:USDT")
for PAIR in "${PAIRS[@]}"; do
    echo "Running Alpha on $PAIR"
    docker run --rm \
      -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data \
      freqtradeorg/freqtrade:develop \
      hyperopt \
      --config user_data/config_alpha.json \
      --hyperopt-loss SharpeHyperOptLoss \
      --strategy ChacalPulseV4_Hyperopt \
      --spaces buy sell roi stoploss \
      --timeframe 5m \
      --timerange 20250101- \
      --epochs 1000 \
      --pairs "$PAIR" \
      --job-workers 1
done

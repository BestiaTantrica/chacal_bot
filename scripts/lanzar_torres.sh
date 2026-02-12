#!/bin/bash
# Actualizar IP DuckDNS (Silencioso y Rapido)
curl -s "https://www.duckdns.org/update?domains=chacal-guru&token=6f2f059c-160c-4cd4-bce0-b7de64bdb2c8" > /dev/null

# Matar todo lo anterior
sudo docker stop chacal_alpha chacal_beta chacal_gamma chacal_delta 2>/dev/null
sudo docker rm chacal_alpha chacal_beta chacal_gamma chacal_delta 2>/dev/null

# Levantar las 4 Torres con config real
sudo docker run -d --name chacal_alpha --rm -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data freqtradeorg/freqtrade:stable trade --strategy ChacalPulseV4_Hyperopt --config user_data/config_alpha.json --db-url sqlite:///user_data/tradesv3_alpha_dry.sqlite
sudo docker run -d --name chacal_beta --rm -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data freqtradeorg/freqtrade:stable trade --strategy ChacalPulseV4_Hyperopt --config user_data/config_beta.json --db-url sqlite:///user_data/tradesv3_beta_dry.sqlite
sudo docker run -d --name chacal_gamma --rm -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data freqtradeorg/freqtrade:stable trade --strategy ChacalPulseV4_Hyperopt --config user_data/config_gamma.json --db-url sqlite:///user_data/tradesv3_gamma_dry.sqlite
sudo docker run -d --name chacal_delta --rm -v /home/ec2-user/chacal_bot/user_data:/freqtrade/user_data freqtradeorg/freqtrade:stable trade --strategy ChacalPulseV4_Hyperopt --config user_data/config_delta.json --db-url sqlite:///user_data/tradesv3_delta_dry.sqlite

# Reiniciar Conserje (Nativo)
pkill -9 -f conserje_v4.py
nohup python3 scripts/conserje_v4.py > conserje.log 2>&1 &

import json
import os

configs = [
    "/home/ec2-user/chacal_bot/user_data/config_alpha.json",
    "/home/ec2-user/chacal_bot/user_data/config_beta.json",
    "/home/ec2-user/chacal_bot/user_data/config_gamma.json",
    "/home/ec2-user/chacal_bot/user_data/config_delta.json"
]

for config_path in configs:
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # 1. Blindaje de Órdenes
        if "order_types" not in data:
            data["order_types"] = {}
        
        data["order_types"]["stoploss_on_exchange"] = True
        data["order_types"]["stoploss_on_exchange_interval"] = 60
        
        # 2. Circuit Breaker de Red/Exchange
        if "exchange" in data:
            # Reintento agresivo y timeout
            data["exchange"]["ccxt_config"] = {"enableRateLimit": True, "options": {"defaultType": "future"}}
            data["exchange"]["ccxt_async_config"] = {
                "concurrency": 2,
                "retries": 3,
                "timeout": 10
            }

        # 3. Protecciones de Estado (Circuit Breaker)
        # Detener si hay fallas consecutivas para no quemar cuotas
        data["protections"] = [
            {
                "method": "StoplossGuard",
                "lookback_period_minutes": 60,
                "trade_limit": 1,
                "stop_duration_minutes": 15,
                "only_per_pair": True
            }
        ]

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"SUCCESS: {os.path.basename(config_path)} blindado.")
    except Exception as e:
        print(f"ERROR en {config_path}: {e}")

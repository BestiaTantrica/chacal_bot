import json
import os

configs = {
    "alpha": ["BTC", "ETH", "SOL"],
    "beta": ["BNB", "XRP", "ADA"],
    "gamma": ["DOGE", "AVAX", "LINK"],
    "delta": ["DOT", "SUI", "NEAR"]
}

base_dir = "user_data/hyperopt_results"

def get_params(coin):
    if coin == "NEAR":
        path = os.path.join(base_dir, "ChacalPulseV4_5m_NEAR_20260208.json")
    else:
        path = os.path.join(base_dir, f"fase2_{coin}.json")
    
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"ERR: No hay datos para {coin}")
        return None
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Buscar el bloque de json al final del archivo si no es puro json
        if '{"params":' in content:
            start = content.find('{"params":')
            return json.loads(content[start:])
        try:
            return json.loads(content)
        except:
            return None

for tower, coins in configs.items():
    config_path = f"user_data/config_{tower}.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        conf = json.load(f)
    
    conf["dry_run_wallet"] = 75
    conf["max_open_trades"] = 3
    conf["stake_amount"] = "unlimited"
    
    # Reconstruir params[buy] y params[sell]
    conf["params"]["buy"] = {}
    conf["params"]["sell"] = {}
    
    # Asumimos que ROI y Stoploss globales se toman de la primera moneda o se dejan
    # Pero el protocolo dice que el ROI y Stoploss son por moneda en V4
    
    for coin in coins:
        p = get_params(coin)
        if p:
            pair = f"{coin}/USDT:USDT"
            conf["params"]["buy"][pair] = {
                "operation_mode": p["params"].get("operation_mode", "hunter"),
                "pulse_change": p["params"].get("pulse_change", 0.005),
                "v_factor": p["params"].get("v_factor", 5.0)
            }
            conf["params"]["sell"][pair] = {
                "bull_roi_0": p["params"].get("bull_roi_0", 0.05),
                "bull_stoploss": p["params"].get("bull_stoploss", -0.05),
                "bear_roi_0": p["params"].get("bear_roi_0", 0.03),
                "bear_stoploss": p["params"].get("bear_stoploss", -0.04),
                "sideways_roi_0": p["params"].get("sideways_roi_0", 0.02),
                "sideways_stoploss": p["params"].get("sideways_stoploss", -0.02)
            }
            # El stoploss general del bot lo usamos del hyperopt
            conf["stoploss"] = p.get("stoploss", -0.25)
            conf["minimal_roi"] = p.get("minimal_roi", {"0": 0.1})

    with open(config_path, 'w') as f:
        json.dump(conf, f, indent=4)
    print(f"OK: {config_path} actualizado.")

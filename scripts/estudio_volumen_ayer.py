import pandas as pd
import json
import os
from datetime import datetime

# Valores oficiales
V_FACTORS = {
    "BTC/USDT:USDT": 4.660,
    "ETH/USDT:USDT": 5.769,
    "SOL/USDT:USDT": 5.386,
    "DOGE/USDT:USDT": 5.795
}

DATA_PATH = "user_data/data/binance"

def analyze_signals(pair, v_factor):
    # Cargar archivo feather o json (ajustar segun formato de freqtrade)
    filename = f"{pair.replace('/', '_').replace(':', '_')}-5m-futures.json"
    full_path = os.path.join(DATA_PATH, filename)
    
    if not os.path.exists(full_path):
        return f"Error: No hay datos para {pair}"
        
    with open(full_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['volume_mean'] = df['volume'].rolling(20).mean()
    df['spike'] = df['volume'] / df['volume_mean']
    
    # Filtrar solo ayer 13 de febrero
    df['date_dt'] = pd.to_datetime(df['date'], unit='ms')
    df_yesterday = df[df['date_dt'].dt.strftime('%Y-%m-%d') == '2026-02-13']
    
    max_spike = df_yesterday['spike'].max()
    signals = df_yesterday[df_yesterday['spike'] > v_factor]
    
    return {
        "pair": pair,
        "max_spike_detected": round(max_spike, 3),
        "v_factor_required": v_factor,
        "signals_triggered": len(signals),
        "status": "✅ OPERÓ" if len(signals) > 0 else "❌ BLOQUEADO POR V_FACTOR"
    }

print("--- ANÁLISIS DE VOLUMEN AYER (2026-02-13) ---")
for pair, v in V_FACTORS.items():
    res = analyze_signals(pair, v)
    print(res)

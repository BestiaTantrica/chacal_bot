import pickle
import json
import os

path = '/freqtrade/user_data/hyperopt_results/strategy_ChacalPulseV4_Hyperopt_2026-02-27_15-33-07.fthypt'

if not os.path.exists(path):
    print(json.dumps({"error": f"Archivo no encontrado: {path}"}))
    exit(1)

try:
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    # Extraer información relevante
    report = {
        "best_result": data.get('best_result', "No hay épocas aún"),
        "total_epochs": len(data.get('results', [])),
        "latest_result": data.get('results', [])[-1] if data.get('results') else "N/A"
    }
    print(json.dumps(report, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))

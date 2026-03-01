import json
import os

path = "/home/ec2-user/chacal_bot/user_data/hyperopt_results/strategy_ChacalPulseV4_Hyperopt_2026-02-27_17-34-01.fthypt"

if not os.path.exists(path):
    print(json.dumps({"error": "Archivo no encontrado"}))
    exit(1)

try:
    with open(path, "r") as f:
        lines = f.readlines()
        if not lines:
            print(json.dumps({"error": "Archivo vacio"}))
            exit(1)
        
        # Freqtrade a veces guarda el JSON completo en cada linea o hace append
        # Buscamos la ultima linea que sea un JSON valido
        for i in range(len(lines)-1, -1, -1):
            line = lines[i].strip()
            if not line: continue
            try:
                data = json.loads(line)
                report = {
                    "epochs": len(data.get("results", [])),
                    "best_loss": data.get("best_loss"),
                    "best_result": data.get("best_result", {}),
                    "last_modified": os.path.getmtime(path)
                }
                print(json.dumps(report, indent=2))
                break
            except:
                continue
except Exception as e:
    print(json.dumps({"error": str(e)}))

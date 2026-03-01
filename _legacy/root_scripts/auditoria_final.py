import json
import os
import time

path = "/freqtrade/user_data/hyperopt_results/strategy_ChacalPulseV4_Hyperopt_2026-02-27_15-33-07.fthypt"

if not os.path.exists(path):
    print("ERROR: El archivo no existe.")
    exit(1)

stats = os.stat(path)
last_mod = time.ctime(stats.st_mtime)

try:
    with open(path, 'r') as f:
        content = f.read()
    
    # Freqtrade a veces concatena JSONs uno tras otro
    # Intentamos parsear el último objeto válido
    blocks = content.strip().split('\n')
    total_epochs = 0
    best_sharpe = "N/A"
    last_epoch = "N/A"
    
    for block in blocks:
        try:
            data = json.loads(block)
            results = data.get("results", [])
            total_epochs += len(results)
            loss = data.get("best_loss")
            if loss is not None and isinstance(loss, (int, float)):
                best_sharpe = -loss
            if results:
                last_epoch = results[-1]
        except:
            continue
            
    report = {
        "file_last_modified_server_time": last_mod,
        "total_epochs_completed": total_epochs,
        "best_sharpe_found": best_sharpe,
        "last_epoch_details": last_epoch
    }
    print(json.dumps(report, indent=2))
except Exception as e:
    print(f"ERROR FATAL: {str(e)}")

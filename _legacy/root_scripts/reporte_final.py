import json
import os

path = "/home/ec2-user/chacal_bot/user_data/hyperopt_results/strategy_ChacalPulseV4_Hyperopt_2026-02-27_17-34-01.fthypt"

def get_report():
    if not os.path.exists(path):
        return {"error": "Archivo no encontrado"}
    
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        
        best_loss = 100
        best_result = {}
        total_epochs = 0
        
        for line in lines:
            line = line.strip()
            if not line: continue
            try:
                data = json.loads(line)
                results = data.get("results", [])
                total_epochs += len(results)
                loss = data.get("best_loss")
                if loss is not None and loss < best_loss:
                    best_loss = loss
                    best_result = data.get("best_result", {})
            except:
                continue
        
        return {
            "epochs": total_epochs,
            "best_sharpe": -best_loss if best_loss != 100 else "N/A",
            "best_result": best_result,
            "status": "OPERATIVO",
            "file_size_mb": os.path.getsize(path) / (1024*1024)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(json.dumps(get_report(), indent=2))

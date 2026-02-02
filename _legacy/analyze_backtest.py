#!/usr/bin/env python3
import json
import zipfile
import sys
import glob

# Buscar el ultimo backtest
results_dir = "/home/ec2-user/chacal_bot/user_data/backtest_results"
files = glob.glob(f'{results_dir}/backtest-result-*.zip')

if not files:
    print("No hay archivos de backtest")
    sys.exit(1)

latest = max(files)
print(f"Archivo: {latest}")

with zipfile.ZipFile(latest, 'r') as z:
    for name in z.namelist():
        if name.endswith('.json'):
            with z.open(name) as f:
                data = json.load(f)
                print(f"Keys: {list(data.keys())}")
                
                # Buscar donde estan las stats
                if 'strategy' in data:
                    print(f"strategy keys: {list(data['strategy'].keys())}")
                elif 'EstrategiaChacal' in data:
                    print(f"EstrategiaChacal encontrado directamente")
                else:
                    # Mostrar estructura
                    for k, v in data.items():
                        if isinstance(v, dict):
                            print(f"  {k}: {list(v.keys())[:5]}")
                        else:
                            print(f"  {k}: {type(v).__name__}")

import os
import json
import glob

# Protocolo Sniper V4: Sincronización de Balance y Estrategia
configs = glob.glob('user_data/config_*.json')
for f in configs:
    if "download" in f: continue
    try:
        with open(f, 'r') as fh:
            data = json.load(fh)
        
        # Unificar Balance a 300 USDT (Dry Run Estándar)
        data['dry_run_wallet'] = 300
        # Asegurar que Telegram esté desactivado en las torres para que no pelen con la Lambda
        if 'telegram' in data:
            data['telegram']['enabled'] = False
        
        with open(f, 'w') as fh:
            json.dump(data, fh, indent=4)
        print(f"Sincronizado {f} (Balance: 300 USDT)")
    except: pass

# Reiniciar torres
os.system("bash lanzar_torres.sh")

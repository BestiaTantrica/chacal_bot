import os
import json
import glob

# Protocolo Sniper V4: Limpieza de Conflictos
configs = glob.glob('user_data/config_*.json')
for f in configs:
    try:
        with open(f, 'r') as fh:
            data = json.load(fh)
        if 'telegram' in data:
            data['telegram']['enabled'] = False
            with open(f, 'w') as fh:
                json.dump(data, fh, indent=4)
        print(f"Desactivado Telegram en {f}")
    except: pass

# Reiniciar torres
os.system("bash lanzar_torres.sh")

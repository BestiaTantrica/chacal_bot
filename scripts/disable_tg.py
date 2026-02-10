import json
import glob
import os

configs = glob.glob('/home/ec2-user/chacal_bot/user_data/config_*.json')
for f in configs:
    if 'download' in f: continue
    try:
        with open(f, 'r') as fh:
            data = json.load(fh)
        if 'telegram' in data:
            data['telegram']['enabled'] = False
        with open(f, 'w') as fh:
            json.dump(data, fh, indent=4)
        print(f"Telegram deshabilitado en: {f}")
    except Exception as e:
        print(f"Error en {f}: {e}")

os.system("bash /home/ec2-user/chacal_bot/lanzar_torres.sh")

import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

TOKEN_CORRECTO = os.getenv("TELEGRAM_TOKEN")
IP_SERVER = "18.231.197.2" # IP actual verificada
KEY_PATH = "llave-sao-paulo.pem"

def fix_configs_remotely():
    print(f"Corrigiendo token a: {TOKEN_CORRECTO}")
    # Comando para corregir el token en todos los config_*.json usando python en el server para mayor seguridad que sed
    py_cmd = f"""
import json, glob
files = glob.glob('/home/ec2-user/chacal_bot/user_data/config_*.json')
for f in files:
    with open(f, 'r') as fh:
        data = json.load(fh)
    data['telegram']['token'] = '{TOKEN_CORRECTO}'
    with open(f, 'w') as fh:
        json.dump(data, fh, indent=4)
    print(f'Corregido: {{f}}')
"""
    # Ejecutar en el server
    cmd = f'ssh -i {KEY_PATH} -o StrictHostKeyChecking=no ec2-user@{IP_SERVER} "python3 -c \\"{py_cmd}\\""'
    os.system(cmd)

def restart_towers():
    print("Reiniciando torres...")
    cmd = f'ssh -i {KEY_PATH} -o StrictHostKeyChecking=no ec2-user@{IP_SERVER} "bash /home/ec2-user/chacal_bot/lanzar_torres.sh"'
    os.system(cmd)

if __name__ == "__main__":
    fix_configs_remotely()
    restart_towers()

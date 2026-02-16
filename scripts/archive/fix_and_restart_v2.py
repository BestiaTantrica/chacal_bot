import os
import json
import subprocess
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

TOKEN_CORRECTO = os.getenv("TELEGRAM_TOKEN")
IP_SERVER = "18.231.197.2"
KEY_PATH = "llave-sao-paulo.pem"
REMOTE_DIR = "/home/ec2-user/chacal_bot/user_data"

def fix_configs_locally_and_upload():
    configs = ["config_alpha.json", "config_beta.json", "config_gamma.json", "config_delta.json"]
    
    for cfg in configs:
        print(f"Descargando {cfg}...")
        # Descargar el archivo
        dl_cmd = f'scp -i {KEY_PATH} -o StrictHostKeyChecking=no ec2-user@{IP_SERVER}:{REMOTE_DIR}/{cfg} {cfg}.tmp'
        subprocess.run(dl_cmd, shell=True)
        
        # Modificar localmente
        try:
            with open(f"{cfg}.tmp", "r") as f:
                data = json.load(f)
            
            data["telegram"]["token"] = TOKEN_CORRECTO
            # Asegurarse que apunte a la estrategia correcta
            data["strategy"] = "ChacalPulseV4_Hyperopt"
            
            with open(f"{cfg}.tmp", "w") as f:
                json.dump(data, f, indent=4)
            
            # Subir
            print(f"Subiendo {cfg} corregido...")
            ul_cmd = f'scp -i {KEY_PATH} -o StrictHostKeyChecking=no {cfg}.tmp ec2-user@{IP_SERVER}:{REMOTE_DIR}/{cfg}'
            subprocess.run(ul_cmd, shell=True)
            
            # Limpiar
            os.remove(f"{cfg}.tmp")
        except Exception as e:
            print(f"Error procesando {cfg}: {e}")

def restart_towers():
    print("Reiniciando torres...")
    cmd = f'ssh -i {KEY_PATH} -o StrictHostKeyChecking=no ec2-user@{IP_SERVER} "bash /home/ec2-user/chacal_bot/lanzar_torres.sh"'
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    fix_configs_locally_and_upload()
    restart_towers()

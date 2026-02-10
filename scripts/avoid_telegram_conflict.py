import os
import json
import subprocess
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

IP_SERVER = "18.231.197.2"
KEY_PATH = "llave-sao-paulo.pem"
REMOTE_DIR = "/home/ec2-user/chacal_bot/user_data"

def disable_telegram_in_secondaries():
    # Solo Alpha mantiene Telegram. Beta, Gamma y Delta se desactivan.
    configs = ["config_beta.json", "config_gamma.json", "config_delta.json"]
    
    for cfg in configs:
        print(f"Descargando {cfg} para desactivar Telegram...")
        subprocess.run(f'scp -i {KEY_PATH} -o StrictHostKeyChecking=no ec2-user@{IP_SERVER}:{REMOTE_DIR}/{cfg} {cfg}.tmp', shell=True)
        
        try:
            with open(f"{cfg}.tmp", "r") as f:
                data = json.load(f)
            
            data["telegram"]["enabled"] = False
            
            with open(f"{cfg}.tmp", "w") as f:
                json.dump(data, f, indent=4)
            
            print(f"Subiendo {cfg} sin Telegram...")
            subprocess.run(f'scp -i {KEY_PATH} -o StrictHostKeyChecking=no {cfg}.tmp ec2-user@{IP_SERVER}:{REMOTE_DIR}/{cfg}', shell=True)
            os.remove(f"{cfg}.tmp")
        except Exception as e:
            print(f"Error en {cfg}: {e}")

def restart_towers():
    print("Reiniciando torres...")
    subprocess.run(f'ssh -i {KEY_PATH} -o StrictHostKeyChecking=no ec2-user@{IP_SERVER} "bash /home/ec2-user/chacal_bot/lanzar_torres.sh"', shell=True)

if __name__ == "__main__":
    disable_telegram_in_secondaries()
    restart_towers()

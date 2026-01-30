import json
import os
import re

# PROTOCOLO CHACAL: Inyección dinámica de secretos
ENV_PATH = '.env.deployment'
CONFIG_PATH = '/home/ec2-user/chacal_bot/user_data/config_chacal_aws.json'

def get_env_secret(key):
    try:
        with open(ENV_PATH, 'r') as f:
            content = f.read()
            match = re.search(f'^{key}=(.*)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return None

def update_secrets():
    tg_token = get_env_secret('TELEGRAM_TOKEN') # O el que esté en .env
    # En el .env.deployment del usuario parece que TELEGRAM no está explícito pero sí BINANCE
    # Vamos a buscar BINANCE_API_KEY y BINANCE_SECRET_KEY
    binance_key = get_env_secret('BINANCE_API_KEY')
    binance_secret = get_env_secret('BINANCE_SECRET_KEY')
    
    # Si no encuentra el token de telegram específico, buscamos en el archivo
    if not tg_token:
        # Intento buscar una línea que parezca un token si no tiene KEY
        with open(ENV_PATH, 'r') as f:
            for line in f:
                if ':' in line and len(line) > 30: # Patrón común de token TG
                    tg_token = line.strip()
                    break

    try:
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
        
        if tg_token:
            data['telegram']['token'] = tg_token
            print("Telegram Token inyectado.")
        
        if binance_key and binance_secret:
            data['exchange']['key'] = binance_key
            data['exchange']['secret'] = binance_secret
            print("Binance Keys inyectadas.")
            
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=4)
            
        print(f"SUCCESS: Secrets updated in {CONFIG_PATH}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        exit(1)

if __name__ == "__main__":
    update_secrets()

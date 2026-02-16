import requests
import os
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
TOKEN = os.getenv('TELEGRAM_TOKEN')
ENDPOINT = 'https://3v0a8ulsif.execute-api.sa-east-1.amazonaws.com'

def set_webhook():
    print(f"Borrando webhook anterior...")
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    
    print(f"Seteando Webhook a: {ENDPOINT}")
    resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={ENDPOINT}")
    print(f"Respuesta: {resp.json()}")

if __name__ == "__main__":
    if TOKEN:
        set_webhook()
    else:
        print("Error: No TOKEN found in .env.aws")

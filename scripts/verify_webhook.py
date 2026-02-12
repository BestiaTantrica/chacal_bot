import requests
import os
import json
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
TOKEN = os.getenv('TELEGRAM_TOKEN')
ENDPOINT = 'https://3v0a8ulsif.execute-api.sa-east-1.amazonaws.com'

def set_final_webhook():
    print(f"Checking Webhook Info...")
    info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
    print(json.dumps(info, indent=2))
    
    if info.get('result', {}).get('url') != ENDPOINT:
        print(f"Setting Webhook to correct endpoint: {ENDPOINT}")
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
        resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={ENDPOINT}")
        print(json.dumps(resp.json(), indent=2))
    else:
        print("Webhook is already correct.")

if __name__ == "__main__":
    if TOKEN:
        set_final_webhook()

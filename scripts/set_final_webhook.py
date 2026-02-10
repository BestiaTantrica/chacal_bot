import requests
import os
from dotenv import load_dotenv

load_dotenv(".env")
TOKEN = os.getenv("TELEGRAM_TOKEN")
URL = "https://sh6dp04q24.execute-api.sa-east-1.amazonaws.com"

def set_final_webhook():
    print(f"Seteando webhook final en {URL}")
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={URL}")
    print(resp.json())

if __name__ == "__main__":
    set_final_webhook()

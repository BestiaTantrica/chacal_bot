import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv('/home/ec2-user/chacal_bot/.env.aws')
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

def ping():
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🦅 CONSERJE V4.2 ONLINE - ¿ME RECIBES? (PING DESDE SERVER)"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            print(r.read().decode())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ping()

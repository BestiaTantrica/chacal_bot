
import json
import requests
import sys
import os

try:
    with open('chacal_bot/config_chacal_aws.json', 'r') as f:
        config = json.load(f)
    
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']
    
    msg = "🐺 *SISTEMA CONFIRMADO* 🐺\n\nConexión establecida desde AWS.\nUse /status para ver estado.\nUse /stop para detener."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    
    resp = requests.post(url, json=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
except Exception as e:
    print(f"Error: {e}")

import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables desde .env.deployment si existe, si no del entorno
load_dotenv(".env.deployment")
token = os.getenv("TELEGRAM_TOKEN")
url = "https://s4n67s9s6i.execute-api.sa-east-1.amazonaws.com"

if not token:
    print("Error: No se encontró TELEGRAM_TOKEN en el entorno o .env.deployment")
    exit(1)

print(f"Configurando Webhook para: {url}")
r = requests.get(f"https://api.telegram.org/bot{token}/setWebhook?url={url}")
print(f"Respuesta: {r.json()}")

info = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
print(f"Estado Webhook: {json.dumps(info.json(), indent=2)}")

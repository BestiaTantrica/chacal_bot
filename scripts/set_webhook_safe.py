import requests
import json

token = "8073681433:AAEB7UQ0BR6y0PI6XrilSmmNL2tX3eCj7rw"
url = "https://s4n67s9s6i.execute-api.sa-east-1.amazonaws.com"

print(f"Configurando Webhook para: {url}")
r = requests.get(f"https://api.telegram.org/bot{token}/setWebhook?url={url}")
print(f"Respuesta: {r.json()}")

info = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
print(f"Estado Webhook: {json.dumps(info.json(), indent=2)}")

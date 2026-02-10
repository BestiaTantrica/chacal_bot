import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

client = boto3.client('lambda', region_name='sa-east-1')
FUNC_NAME = "chacal_bot_v2"
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

event = {
    "body": json.dumps({
        "message": {
            "chat": {"id": int(CHAT_ID)},
            "text": "/reporte"
        }
    })
}

print(f"Probando Lambda {FUNC_NAME} con /reporte...")
resp = client.invoke(
    FunctionName=FUNC_NAME,
    Payload=json.dumps(event)
)

print(f"Status: {resp['StatusCode']}")
payload = json.loads(resp['Payload'].read())
print(f"Response: {payload}")

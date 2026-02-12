import boto3
import json
import os
import base64
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

def invoke_lambda():
    print("--- INVOKING LAMBDA DIRECTLY ---")
    
    # Payload simulando un mensaje de Telegram /status
    payload = {
        "body": json.dumps({
            "message": {
                "chat": {"id": int(CHAT_ID)},
                "text": "/status"
            }
        })
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='chacal_bot_v2',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )
        
        status = response['StatusCode']
        print(f"StatusCode: {status}")
        
        if 'FunctionError' in response:
            print(f"FunctionError: {response['FunctionError']}")
            
        logs = base64.b64decode(response['LogResult']).decode('utf-8')
        print("\n--- EXECUTION LOGS ---")
        print(logs)
        
        payload_resp = response['Payload'].read().decode('utf-8')
        print(f"\nResponse Payload: {payload_resp}")
        
    except Exception as e:
        print(f"Invocation Error: {e}")

if __name__ == "__main__":
    if CHAT_ID:
        invoke_lambda()
    else:
        print("Missing CHAT_ID")

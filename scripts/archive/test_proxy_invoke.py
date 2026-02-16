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

def invoke_proxy_simulation():
    print("--- INVOKING LAMBDA WITH PROXY EVENT ---")
    
    # Body as string, mimicking API Gateway Proxy
    body_content = json.dumps({
        "message": {
            "chat": {"id": int(CHAT_ID)},
            "text": "/status (Proxy Test)"
        }
    })
    
    # Proxy Integration Event Structure
    payload = {
        "resource": "/",
        "path": "/",
        "httpMethod": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": body_content,
        "isBase64Encoded": False
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='chacal_bot_v2',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )
        
        status = response['StatusCode']
        print(f"AWS Invoke StatusCode: {status}")
        
        if 'FunctionError' in response:
            print(f"FunctionError: {response['FunctionError']}")
            
        logs = base64.b64decode(response['LogResult']).decode('utf-8')
        # print(logs) # Only print if needed
        
        payload_resp = json.loads(response['Payload'].read().decode('utf-8'))
        print("\n--- RESPONSE PAYLOAD ---")
        print(json.dumps(payload_resp, indent=2))
        
        # Verify structure
        if 'statusCode' in payload_resp and 'body' in payload_resp and 'headers' in payload_resp:
             print("\nSUCCESS: Response structure matches API Gateway Proxy requirements.")
        else:
             print("\nFAILURE: Response structure incorrect for Proxy Integration.")
        
    except Exception as e:
        print(f"Invocation Error: {e}")

if __name__ == "__main__":
    if CHAT_ID:
        invoke_proxy_simulation()

import boto3
import os
import json
import zipfile
import io
from dotenv import load_dotenv

# Load env from c:\Freqtrade\.env.aws
load_dotenv('c:/Freqtrade/.env.aws')

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
apigateway = boto3.client('apigatewayv2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

MACRO_LAMBDA_CODE = r'''
import os
import json
import boto3
import urllib.request
import urllib.parse
import time

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
INSTANCE_ID = os.environ['INSTANCE_ID']
CHAT_ID = os.environ['CHAT_ID']

ec2 = boto3.client('ec2', region_name='sa-east-1')
ssm = boto3.client('ssm', region_name='sa-east-1')

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    data = urllib.parse.urlencode(payload).encode()
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Telegram error: {e}")

def lambda_handler(event, context):
    print(f"EVENT: {json.dumps(event)}")
    
    # Logic for EventBridge
    if event.get('action') == 'START_SERVER_AUTO':
        print("Starting server via EventBridge...")
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        return {'statusCode': 200, 'body': 'Server auto-started'}

    try:
        body = json.loads(event.get('body', '{}'))
        if 'message' not in body: return {'statusCode': 200}
        chat_id = str(body['message']['chat']['id'])
        text = body['message'].get('text', '').lower()
        
        if chat_id != CHAT_ID: return {'statusCode': 200}

        # Comandos de Reporte (Unificados: /status, /reporte, flash)
        is_report_cmd = any(cmd in text for cmd in ['/status', '/reporte', 'flash', 'informe', 'status'])
        
        if is_report_cmd:
            resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
            state = resp['Reservations'][0]['Instances'][0]['State']['Name']
            
            if state == 'running':
                send_telegram("⚡ <b>Sniper V4: Generando reporte técnico instantáneo...</b>")
                cmd = "python3 /home/ec2-user/chacal_bot/scripts/diagnostico_fast.py"
                try:
                    ssm_resp = ssm.send_command(
                        InstanceIds=[INSTANCE_ID],
                        DocumentName="AWS-RunShellScript",
                        Parameters={'commands': [cmd]}
                    )
                    command_id = ssm_resp['Command']['CommandId']
                    time.sleep(4) # Wait a bit for execution
                    output = ssm.get_command_invocation(CommandId=command_id, InstanceId=INSTANCE_ID)
                    reporte = output['StandardOutputContent']
                    if reporte.strip():
                        send_telegram(f"🛰️ <b>SISTEMA SNIPER V4 (UNIFICADO)</b>\n{reporte}")
                        return {'statusCode': 200}
                    else:
                         send_telegram("⚠️ El reporte llegó vacío. Reintenta.")
                except Exception as e:
                    send_telegram(f"⚠️ Error intentando SSM: {e}")
            else:
                send_telegram("⚡ <b>Sniper V4: Procesando consulta técnica...</b>\n💤 Servidor APAGADO (Ahorro Energía). Encendiendo torre para reporte flash...")
                ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'FLASH'}])
                ec2.start_instances(InstanceIds=[INSTANCE_ID])
                
        elif '/hyperopt' in text:
            send_telegram("🧬 <b>Iniciando Motor Hyperopt...</b>")
            ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'HYPEROPT'}])
            ec2.start_instances(InstanceIds=[INSTANCE_ID])
        
        elif '/start' in text:
             send_telegram("🦅 <b>Chacal Bot V4 (Serverless Brain)</b>\nEstoy en la nube. Si el servidor está apagado, un /status me despierta.")
                
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 200}
'''

def update_lambda_code():
    print("Zipping new code...")
    zip_output = io.BytesIO()
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', MACRO_LAMBDA_CODE)
    zip_output.seek(0)
    
    print("Updating Lambda Code for 'chacal_bot_v2'...")
    try:
        lambda_client.update_function_code(
            FunctionName='chacal_bot_v2',
            ZipFile=zip_output.read()
        )
        print("Lambda updated successfully.")
    except Exception as e:
        print(f"Error updating lambda: {e}")

def get_api_endpoint():
    print("Searching for API Gateway...")
    try:
        apis = apigateway.get_apis()
        for item in apis['Items']:
            if 'chacal' in item['Name'].lower() or 'bot' in item['Name'].lower():
                print(f"FOUND API: {item['Name']}")
                endpoint = item['ApiEndpoint']
                print(f"ENDPOINT: {endpoint}")
                return endpoint
        print("No match found in APIs.")
    except Exception as e:
        print(f"Error listing APIs: {e}")

if __name__ == "__main__":
    update_lambda_code()
    endpoint = get_api_endpoint()
    
    if endpoint:
        # Save to file so we can read it in next step
        with open("c:/Freqtrade/api_endpoint.txt", "w") as f:
            f.write(endpoint)

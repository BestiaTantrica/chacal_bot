import boto3
import os
import json
import zipfile
import io
from dotenv import load_dotenv

# Load env
load_dotenv('c:/Freqtrade/.env.aws')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

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
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        data = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

def lambda_handler(event, context):
    print(f"EVENT: {json.dumps(event)}")
    
    try:
        # EventBridge Trigger
        if event.get('action') == 'START_SERVER_AUTO':
            print("Starting server via EventBridge...")
            ec2.start_instances(InstanceIds=[INSTANCE_ID])
            return {'statusCode': 200, 'body': 'Server auto-started'}

        # Parsing Body
        body_str = event.get('body', '{}')
        if not body_str: body_str = '{}'
        
        try:
            body = json.loads(body_str)
        except:
             # If body is not valid JSON, just return 200 to clear webhook
             print("Invalid JSON body")
             return {'statusCode': 200}

        if 'message' not in body: return {'statusCode': 200}
        
        chat_id = str(body['message']['chat']['id'])
        # Loose check for chat_id (convert everything to string)
        if str(chat_id) != str(CHAT_ID): 
            print(f"Unauthorized Chat ID: {chat_id}")
            return {'statusCode': 200}

        text = body['message'].get('text', '').lower()
        print(f"Received Command: {text}")

        # Comandos de Reporte
        is_report_cmd = any(cmd in text for cmd in ['/status', '/reporte', 'flash', 'informe'])
        
        if is_report_cmd:
            resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
            state = resp['Reservations'][0]['Instances'][0]['State']['Name']
            print(f"Instance State: {state}")
            
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
                    # Wait loop
                    for _ in range(5):
                        time.sleep(2)
                        output = ssm.get_command_invocation(CommandId=command_id, InstanceId=INSTANCE_ID)
                        if output['Status'] in ['Success', 'Failed']:
                            break
                    
                    reporte = output.get('StandardOutputContent', '')
                    if reporte.strip():
                        send_telegram(f"🛰️ <b>SISTEMA SNIPER V4</b>\n{reporte}")
                    else:
                        send_telegram("⚠️ Reporte vacío (SSM Success but no output).")
                        
                except Exception as e:
                    send_telegram(f"⚠️ Error SSM: {e}")
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

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        # Always return 200 to prevent Telegram retry loop
        return {'statusCode': 200}
        
    return {'statusCode': 200}
'''

def update_lambda_code():
    print("Zipping new robust code...")
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

if __name__ == "__main__":
    update_lambda_code()

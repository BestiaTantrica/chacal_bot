import boto3
import os
import json
import zipfile
import io
import time
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

def respond(status, body):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body),
        'isBase64Encoded': False
    }

def lambda_handler(event, context):
    print(f"EVENT: {json.dumps(event)}")
    
    try:
        # EventBridge: Auto Start
        if event.get('action') == 'START_SERVER_AUTO':
            ec2.start_instances(InstanceIds=[INSTANCE_ID])
            return respond(200, {'message': 'Server auto-started'})

        # Telegram Parse
        body_str = event.get('body', '{}') or '{}'
        try:
            body = json.loads(body_str)
        except:
             return respond(200, {'message': 'Invalid JSON'})

        if 'message' not in body: return respond(200, {'message': 'No message'})
        
        chat_id = str(body['message']['chat']['id'])
        if str(chat_id) != str(CHAT_ID): 
            return respond(200, {'message': 'Unauthorized'})

        text = body['message'].get('text', '').lower()

        # Comandos de Reporte
        is_report_cmd = any(cmd in text for cmd in ['/status', '/reporte', 'flash', 'informe'])
        is_kill_cmd = any(cmd in text for cmd in ['/kill', '/off', '/stop', 'apagar'])
        
        if is_kill_cmd:
            send_telegram("🛑 <b>KILL-SWITCH ACTIVADO</b>\nSolicitando apagado directo de la instancia vía AWS API...")
            ec2.stop_instances(InstanceIds=[INSTANCE_ID])
            return respond(200, {'message': 'Kill command executed'})

        if is_report_cmd:
            resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
            state = resp['Reservations'][0]['Instances'][0]['State']['Name']
            print(f"Instance State: {state}")
            
            if state == 'running':
                # COMMAND: Safe Git Pull -> Run Diagnostico
                # Preserve local truth. Avoid destructive resets.
                cmd = "runuser -l ec2-user -c 'cd /home/ec2-user/chacal_bot && git pull origin main && python3 scripts/diagnostico_fast.py'"
                
                try:
                    ssm_resp = ssm.send_command(
                        InstanceIds=[INSTANCE_ID],
                        DocumentName="AWS-RunShellScript",
                        Parameters={'commands': [cmd]},
                        TimeoutSeconds=30
                    )
                    command_id = ssm_resp['Command']['CommandId']
                    
                    # Esperar resultado (Polling breve)
                    output_text = ""
                    error_text = ""
                    status = "Pending"
                    
                    for _ in range(25): # 25s wait max
                        time.sleep(1)
                        out = ssm.get_command_invocation(CommandId=command_id, InstanceId=INSTANCE_ID)
                        status = out['Status']
                        
                        if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                            output_text = out.get('StandardOutputContent', '')
                            error_text = out.get('StandardErrorContent', '')
                            break
                    
                    if output_text.strip():
                        send_telegram(f"🛰️ <b>SISTEMA SNIPER V4</b>\n{output_text}")
                    elif error_text.strip():
                        send_telegram(f"⚠️ <b>Error en Comando:</b>\n{error_text}")
                    elif status == 'Failed':
                        send_telegram("⚠️ <b>Error Crítico:</b> El comando falló sin dejar rastro.")
                    else:
                        send_telegram("⏳ <b>Actualizando Sistema...</b> (El servidor despertó, reintente en 30s)")
                        
                except ssm.exceptions.InvalidInstanceId:
                    send_telegram("🔌 <b>Despertando...</b> (Auto-Update en progreso)")
                except Exception as e:
                    error_str = str(e)
                    if "InvalidInstanceId" in error_str or "Instances not in a valid state" in error_str:
                         send_telegram("🔌 <b>Despertando...</b> (Auto-Update en progreso)")
                    else:
                        send_telegram(f"⚠️ Error Técnico: {e}")
            
            elif state == 'pending':
                send_telegram("⏳ <b>Servidor 'Pending'...</b> Ya casi estamos.")
                
            else: # stopped, stopping
                send_telegram("⚡ <b>Recibido.</b>\n💤 El servidor estaba DORMIDO. Iniciando secuencia de encendido...")
                ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'FLASH'}])
                ec2.start_instances(InstanceIds=[INSTANCE_ID])
                
        elif '/start' in text:
             send_telegram("🦅 <b>Chacal Bot V4 (Serverless)</b>\nEstoy vivo. Tirá /status.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return respond(200, {'message': 'Error handled'})
        
    return respond(200, {'message': 'OK'})
'''

def update_lambda_code():
    print("Zipping AUTO-UPDATE code...")
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
        
        print("Waiting 10s for consistency...")
        time.sleep(10)

        print("Updating Lambda Configuration (Timeout=60s)...")
        lambda_client.update_function_configuration(
            FunctionName='chacal_bot_v2',
            Timeout=60
        )
        print("Configuration updated.")
    except Exception as e:
        print(f"Error updating lambda: {e}")

if __name__ == "__main__":
    update_lambda_code()

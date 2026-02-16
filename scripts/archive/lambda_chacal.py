import os
import json
import boto3
import urllib.request
import urllib.parse
import time
from datetime import datetime, timezone

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
    
    if event.get('action') == 'START_SERVER_AUTO':
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        return {'statusCode': 200, 'body': 'Server started'}

    try:
        body = json.loads(event.get('body', '{}'))
        if 'message' not in body: return {'statusCode': 200}
        chat_id = str(body['message']['chat']['id'])
        text = body['message'].get('text', '').lower()
        
        if chat_id != CHAT_ID: return {'statusCode': 200}

        # Comandos de Reporte (Unificados: /status, /reporte, flash)
        is_report_cmd = any(cmd in text for cmd in ['/status', '/reporte', 'flash', 'informe'])
        
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
                    time.sleep(3)
                    output = ssm.get_command_invocation(CommandId=command_id, InstanceId=INSTANCE_ID)
                    reporte = output['StandardOutputContent']
                    if reporte.strip():
                        send_telegram(f"🛰️ <b>SISTEMA SNIPER V4 (UNIFICADO)</b>\n{reporte}")
                        return {'statusCode': 200}
                except: pass
                send_telegram("⚠️ Servidor ocupado o procesando. Reintenta en unos segundos.")
            else:
                send_telegram("⚡ <b>Sniper V4: Procesando consulta técnica...</b>\n💤 Fuera de horario. Encendiendo torre para reporte flash...")
                ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'FLASH'}])
                ec2.start_instances(InstanceIds=[INSTANCE_ID])
                
        elif '/hyperopt' in text:
            send_telegram("🧬 <b>Iniciando Motor Hyperopt...</b>")
            ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'HYPEROPT'}])
            ec2.start_instances(InstanceIds=[INSTANCE_ID])
                
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 200}

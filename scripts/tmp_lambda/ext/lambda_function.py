import os
import json
import boto3
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Configuración (Variables de Entorno)
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
INSTANCE_ID = os.environ['INSTANCE_ID']
CHAT_ID = os.environ['CHAT_ID']

ec2 = boto3.client('ec2', region_name='sa-east-1')

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}).encode()
    try:
        urllib.request.urlopen(url, data=data)
    except: pass

def is_dead_hour():
    # Lógica espejo de vigilante_energia.py
    # Rango 1: [10:15 - 13:25] UTC
    # Rango 2: [17:45 - 07:55] UTC
    
    now = datetime.now(timezone.utc)
    
    # Rango 1
    if (now.hour == 10 and now.minute >= 15) or (10 < now.hour < 13) or (now.hour == 13 and now.minute < 25):
        return True
        
    # Rango 2
    if (now.hour >= 18) or (now.hour < 7) or (now.hour == 17 and now.minute >= 45) or (now.hour == 7 and now.minute < 55):
        return True
        
    return False

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        if 'message' not in body: return {'statusCode': 200}
        
        chat_id = str(body['message']['chat']['id'])
        text = body['message'].get('text', '').lower()
        
        if chat_id != CHAT_ID: return {'statusCode': 200}
        
        # VALIDAR HORARIO (Solo permitido en Horas Muertas)
        if not is_dead_hour():
             send_telegram("⛔ **Acceso Denegado:** Estamos en **Horario de Trading Activo**.\nEspera a las Horas Muertas (Magic Hours) para usar estos botones.")
             return {'statusCode': 200}

        mode = None
        if '/reporte' in text or 'flash' in text:
            mode = 'FLASH'
            msg = "⚡ **Iniciando Reporte Flash...**"
        elif '/hyperopt' in text:
            mode = 'HYPEROPT'
            msg = "🧬 **Iniciando Hyperopt...**"
        
        if mode:
            send_telegram(msg)
            # 1. Taggear Instancia
            ec2.create_tags(
                Resources=[INSTANCE_ID],
                Tags=[{'Key': 'MODE', 'Value': mode}]
            )
            # 2. Encender Instancia
            ec2.start_instances(InstanceIds=[INSTANCE_ID])
        
        return {'statusCode': 200}
            
    except Exception as e:
        print(e)
        return {'statusCode': 500}

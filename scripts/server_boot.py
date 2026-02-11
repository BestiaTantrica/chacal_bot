import os
import boto3
import time
import subprocess
from dotenv import load_dotenv

# Configurar rutas absolutas
BASE_DIR = "/home/ec2-user/chacal_bot"
ENV_PATH = os.path.join(BASE_DIR, ".env.aws")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# Cargar credenciales para consultar tags
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    # Ruta local de Windows para pruebas
    load_dotenv(os.path.join('c:/Freqtrade', '.env.aws'))

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

def get_instance_mode():
    if not AWS_ID or not AWS_KEY or not INSTANCE_ID:
        return 'NORMAL'
    try:
        ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
        for tag in tags:
            if tag['Key'] == 'MODE':
                return tag['Value']
    except Exception as e:
        print(f"Error fetching tags: {e}")
    return 'NORMAL'

def run_flash_report():
    print("MODO FLASH DETECTADO")
    # 1. Determinar ruta del script de diagnostico
    diag_script = os.path.join(SCRIPTS_DIR, "diagnostico_fast.py")
    if not os.path.exists(diag_script):
        diag_script = os.path.join("c:/Freqtrade/scripts", "diagnostico_fast.py")

    # 2. Ejecutar y capturar salida
    try:
        result = subprocess.run(["python", diag_script], capture_output=True, text=True).stdout
        if not result:
            result = "INFO: El diagnostico no genero salida."
    except Exception as e:
        result = f"ERROR: Fallo ejecucion diagnostico: {e}"
    
    # 3. Enviar a Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Fallback a .env local
    if not TELEGRAM_TOKEN:
        load_dotenv(os.path.join('c:/Freqtrade', '.env'))
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        
    if TELEGRAM_TOKEN and CHAT_ID:
        import urllib.parse, urllib.request
        data = urllib.parse.urlencode({
            "chat_id": CHAT_ID, 
            "text": result, 
            "parse_mode": "HTML"
        }).encode()
        
        try:
            req = urllib.request.Request(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=data)
            with urllib.request.urlopen(req, timeout=15) as response:
                print(f"OK: Reporte enviado a Telegram.")
        except Exception as e:
            try:
                data_plain = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": result}).encode()
                urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=data_plain, timeout=15)
                print(f"OK: Reporte enviado (Texto Plano).")
            except:
                print(f"ERROR: Fallo total envio Telegram.")
        
    # 4. APAGAR REAL
    if AWS_ID and AWS_KEY and INSTANCE_ID:
        print("Iniciando apagado automatico...")
        try:
            ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
            ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'NORMAL'}])
            ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        except Exception as e:
            print(f"ERROR: Fallo apagado AWS: {e}")

def run_hyperopt():
    print("MODO HYPEROPT")
    run_flash_report()

def run_default():
    print("MODO TRADING ACTIVO")
    pass

if __name__ == "__main__":
    mode = os.getenv("OVERRIDE_MODE") or get_instance_mode()
    print(f"Iniciando en modo: {mode}")
    
    if mode == 'FLASH':
        run_flash_report()
    elif mode == 'HYPEROPT':
        run_hyperopt()
    else:
        run_default()

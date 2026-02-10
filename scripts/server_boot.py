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
load_dotenv(ENV_PATH)
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

def get_instance_mode():
    try:
        ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
        for tag in tags:
            if tag['Key'] == 'MODE':
                return tag['Value']
    except Exception as e:
        print(f"Error fetching tags: {e}")
    return None

def run_flash_report():
    print("⚡ MODO FLASH DETECTADO")
    # 1. Ejecutar diagnostico
    diag_script = os.path.join(SCRIPTS_DIR, "diagnostico_fast.py")
    subprocess.run(["python3", diag_script])
    
    # 2. Enviar a Telegram (diagnostico ya lo hace si tiene credenciales, pero aseguramos)
    # diagnostico_fast.py imprime el resultado, deberiamos capturarlo y enviarlo si no lo hace.
    # Asumimos que diagnostico_fast.py imprime a stdout.
    # El script original de diagnostico_fast.py SOLO imprime. No envia.
    # Necesitamos enviarlo aqui.
    
    # Re-leer salida
    result = subprocess.run(["python3", diag_script], capture_output=True, text=True).stdout
    
    # Enviar (usando curl simple para no depender de librerias extra si faltan)
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    if not TELEGRAM_TOKEN:
        # Intentar cargar de .env normal
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        
    if TELEGRAM_TOKEN and CHAT_ID:
        import urllib.parse, urllib.request
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": result, "parse_mode": "HTML"}).encode()
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=data)
        except: pass
        
    # 3. APAGAR
    print("💤 Apagando servidor...")
    ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    ec2.stop_instances(InstanceIds=[INSTANCE_ID])

def run_hyperopt():
    print("🧬 MODO HYPEROPT DETECTADO")
    # Logica placeholder para Hyperopt
    # subprocess.run(["bash", "/path/to/hyperopt.sh"])
    
    # Por ahora solo avisar y apagar para probar
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    if not TELEGRAM_TOKEN:
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        
    if TELEGRAM_TOKEN and CHAT_ID:
        import urllib.parse, urllib.request
        msg = "🚀 Hyperopt Mode initiated (Placeholder). Shutting down..."
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg}).encode()
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=data)
        except: pass

    # APAGAR
    ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    ec2.stop_instances(InstanceIds=[INSTANCE_ID])


def run_default():
    print("✅ MODO NORMAL (TRADING)")
    # Ejecutar script maestro de trading
    subprocess.Popen(["bash", os.path.join(BASE_DIR, "lanzar_torres.sh")])

if __name__ == "__main__":
    # Esperar red
    time.sleep(10)
    
    mode = get_instance_mode()
    print(f"Boot Mode: {mode}")
    
    if mode == 'FLASH':
        run_flash_report()
    elif mode == 'HYPEROPT':
        run_hyperopt()
    else:
        run_default()

import paramiko
import os
import time
import boto3
from dotenv import load_dotenv

load_dotenv(".env.aws")
KEY_FILE = "llave-sao-paulo.pem"

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

def get_instance_ip():
    ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    try:
        ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        return ip, state
    except:
        return None, "unknown"

def start_server():
    print("Prendiendo servidor para instalar...")
    ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    
    for i in range(20):
        time.sleep(10)
        ip, state = get_instance_ip()
        print(f"Estado: {state} IP: {ip}")
        if state == 'running' and ip:
            return ip
    return None

def install():
    ip, state = get_instance_ip()
    if state != 'running':
        ip = start_server()
    
    if not ip:
        print("Error: No se pudo iniciar el servidor.")
        return

    print(f"Conectando a {ip}...")
    k = paramiko.RSAKey.from_private_key_file(KEY_FILE)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Retry SSH connection
    connected = False
    for i in range(10):
        try:
            c.connect(hostname=ip, username="ec2-user", pkey=k, timeout=10)
            connected = True
            break
        except Exception as e:
            print(f"Intento SSH {i+1} fallido: {e}")
            time.sleep(10)

    if not connected:
        print("Error Critical: No SSH connection.")
        return
    
    try:        
        sftp = c.open_sftp()
        
        # 1. Upload scripts
        print("Subiendo scripts...")
        try: sftp.stat("/home/ec2-user/chacal_bot/scripts")
        except: c.exec_command("mkdir -p /home/ec2-user/chacal_bot/scripts")

        sftp.put("scripts/server_boot.py", "/home/ec2-user/chacal_bot/scripts/server_boot.py")
        sftp.put("scripts/diagnostico_fast.py", "/home/ec2-user/chacal_bot/scripts/diagnostico_fast.py")
        
        # 2. Upload credentials (SEGURO)
        print("Subiendo credenciales...")
        sftp.put(".env.aws", "/home/ec2-user/chacal_bot/.env.aws")
        
        # 3. Install dependencies on server
        print("Instalando dependencias en servidor...")
        c.exec_command("sudo pip3 install boto3 python-dotenv")
        
        # 4. Configurar Cron @reboot
        print("Configurando Auto-Start...")
        # Remove old entry if exists using grep -v
        cmd = "(crontab -l 2>/dev/null | grep -v 'server_boot.py'; echo '@reboot /usr/bin/python3 /home/ec2-user/chacal_bot/scripts/server_boot.py >> /home/ec2-user/boot.log 2>&1') | crontab -"
        c.exec_command(cmd)
        
        print("Instalacion Completa.")
        c.close()
        
        # Stop server to finish
        print("Apagando servidor...")
        ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        print("Servidor apagado. Listo para Telegram.")
        
    except Exception as e:
        print(f"Error durante instalacion: {e}")

if __name__ == "__main__":
    install()

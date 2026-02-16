import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv(".env.aws")
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

print(f"Iniciando instancia {INSTANCE_ID}...")
ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

# 1. Quitar modo FLASH para que no se apague al bootear
ec2.create_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE', 'Value': 'REPAIR'}])

# 2. Start
ec2.start_instances(InstanceIds=[INSTANCE_ID])

print("Esperando a que la instancia esté 'running'...")
while True:
    resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    state = resp['Reservations'][0]['Instances'][0]['State']['Name']
    if state == 'running':
        ip = resp['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        print(f"Instancia levantada! IP: {ip}")
        break
    time.sleep(5)

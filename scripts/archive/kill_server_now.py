import boto3
import os
from dotenv import load_dotenv

load_dotenv('.env.aws')
aws_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_key = os.getenv('AWS_SECRET_ACCESS_KEY')
inst_id = 'i-003dcde3a3dadd6ea'

ec2 = boto3.client('ec2', region_name='sa-east-1', aws_access_key_id=aws_id, aws_secret_access_key=aws_key)

print(f"Solicitando apagado de la instancia: {inst_id}...")
try:
    # Cambiar TAG para evitar que el Vigilante lo despierte si hay lógica de re-encendido
    ec2.create_tags(Resources=[inst_id], Tags=[{'Key': 'MODE', 'Value': 'NORMAL'}])
    
    # Detener instancia
    resp = ec2.stop_instances(InstanceIds=[inst_id])
    state = resp['StoppingInstances'][0]['CurrentState']['Name']
    print(f"Éxito. Estado actual: {state}")
except Exception as e:
    print(f"Error al apagar: {e}")

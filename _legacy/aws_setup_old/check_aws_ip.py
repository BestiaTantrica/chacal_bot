import boto3
import os
from dotenv import load_dotenv

# Cargar credenciales
load_dotenv('.env.aws')

access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
instance_id = os.getenv('AWS_INSTANCE_ID')
region = 'sa-east-1' # Basado en la llave-sao-paulo.pem y la bitácora

ec2 = boto3.client(
    'ec2',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name=region
)

def get_status():
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    state = instance['State']['Name']
    public_ip = instance.get('PublicIpAddress', 'N/A')
    print(f"Instancia: {instance_id}")
    print(f"Estado: {state}")
    print(f"IP Pública: {public_ip}")

if __name__ == "__main__":
    get_status()

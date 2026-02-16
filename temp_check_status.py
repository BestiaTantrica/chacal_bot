import boto3
import os
from dotenv import load_dotenv

# Cargar entorno con ruta absoluta
load_dotenv('C:/Freqtrade/.env.aws')

try:
    ec2 = boto3.client('ec2', region_name='sa-east-1',
                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))

    resp = ec2.describe_instances(InstanceIds=['i-003dcde3a3dadd6ea'])
    state = resp['Reservations'][0]['Instances'][0]['State']['Name']
    print(f"ESTADO_AWS: {state}")
except Exception as e:
    print(f"ERROR: {e}")

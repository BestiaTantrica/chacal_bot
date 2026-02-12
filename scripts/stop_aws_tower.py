import boto3
import os
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')

def stop_instance(instance_id):
    ec2 = boto3.client(
        'ec2',
        region_name='sa-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    print(f"Apagando instancia {instance_id} para test de auto-encendido...")
    ec2.stop_instances(InstanceIds=[instance_id])
    print("Instancia en proceso de apagado.")

if __name__ == "__main__":
    instance_id = os.getenv('AWS_INSTANCE_ID')
    stop_instance(instance_id)

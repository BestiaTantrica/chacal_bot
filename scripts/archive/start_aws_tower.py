import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')

def start_instance_and_get_ip(instance_id):
    ec2 = boto3.client(
        'ec2',
        region_name='sa-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    print(f"Iniciando instancia {instance_id}...")
    ec2.start_instances(InstanceIds=[instance_id])
    
    # Esperar a que esté running
    while True:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                status = instance['State']['Name']
                ip = instance.get('PublicIpAddress')
                print(f"Status actual: {status}, IP: {ip}")
                if status == 'running' and ip:
                    print(f"INSTANCIA_READY_IP: {ip}")
                    return ip
        time.sleep(5)

if __name__ == "__main__":
    instance_id = os.getenv('AWS_INSTANCE_ID')
    start_instance_and_get_ip(instance_id)

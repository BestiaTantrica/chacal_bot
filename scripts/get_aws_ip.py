import boto3
import os
from dotenv import load_dotenv

def get_instance_ip(instance_id, region):
    # Cargar credenciales desde .env.aws
    load_dotenv('c:/Freqtrade/.env.aws')
    
    ec2 = boto3.client(
        'ec2',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        return ip
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    instance_id = "i-003dcde3a3dadd6ea"
    region = "sa-east-1"
    ip = get_instance_ip(instance_id, region)
    print(f"IP_ENCONTRADA:{ip}")

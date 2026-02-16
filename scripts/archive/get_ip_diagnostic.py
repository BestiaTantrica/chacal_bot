import boto3
import os
from dotenv import load_dotenv

load_dotenv('.env.aws')

def get_instance_ip():
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='sa-east-1'
    )
    ec2 = session.resource('ec2')
    instance_id = os.getenv('AWS_INSTANCE_ID')
    instance = ec2.Instance(instance_id)
    
    print(f"Instancia: {instance_id}")
    print(f"Estado: {instance.state['Name']}")
    print(f"IP Pública: {instance.public_ip_address}")
    return instance.public_ip_address

if __name__ == "__main__":
    get_instance_ip()

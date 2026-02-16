import boto3
import os
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')

def check_instance_status(instance_id):
    ec2 = boto3.client(
        'ec2',
        region_name='sa-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    response = ec2.describe_instances(InstanceIds=[instance_id])
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            status = instance['State']['Name']
            ip = instance.get('PublicIpAddress')
            print(f"STATUS: {status}")
            print(f"IP: {ip}")
            return status, ip

if __name__ == "__main__":
    instance_id = os.getenv('AWS_INSTANCE_ID')
    check_instance_status(instance_id)

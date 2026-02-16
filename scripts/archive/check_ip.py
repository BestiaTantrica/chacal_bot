import boto3, os
from dotenv import load_dotenv
load_dotenv('.env.aws')
ec2 = boto3.client('ec2', region_name='sa-east-1', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
resp = ec2.describe_instances(InstanceIds=[os.getenv('AWS_INSTANCE_ID')])
inst = resp['Reservations'][0]['Instances'][0]
print(f"Status: {inst['State']['Name']}")
print(f"IP: {inst.get('PublicIpAddress', 'N/A')}")

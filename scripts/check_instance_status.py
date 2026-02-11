import boto3
import os
from dotenv import load_dotenv

load_dotenv(".env.aws")
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
instance = resp['Reservations'][0]['Instances'][0]
state = instance['State']['Name']
ip = instance.get('PublicIpAddress', 'No IP')
print(f"Instance {INSTANCE_ID} state: {state}")
print(f"Public IP: {ip}")

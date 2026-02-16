import boto3
import os
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')

def check_status():
    try:
        ec2 = boto3.client(
            'ec2',
            region_name='sa-east-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        instance_id = os.getenv('INSTANCE_ID')
        # If INSTANCE_ID is not in .env.aws (it might be AWS_INSTANCE_ID based on user's .env.aws, let's try both or hardcode if known but better to read .env)
        # Based on previous viewed files, .env.aws had INSTANCE_ID=i-003dcde3a3dadd6ea
        
        if not instance_id:
             # Fallback or check AWS_INSTANCE_ID
             instance_id = os.getenv('AWS_INSTANCE_ID')
        
        if not instance_id:
            instance_id = 'i-003dcde3a3dadd6ea' # Hardcoded fallback based on earlier context

        resp = ec2.describe_instances(InstanceIds=[instance_id])
        state = resp['Reservations'][0]['Instances'][0]['State']['Name']
        print(f"INSTANCE_STATE: {state}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()

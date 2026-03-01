import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv("C:/Freqtrade/.env.aws")

ssm = boto3.client(
    'ssm',
    region_name="sa-east-1",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

instance_id = os.getenv('AWS_INSTANCE_ID')

def run_command(cmd):
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [cmd]}
    )
    command_id = response['Command']['CommandId']
    time.sleep(5)
    output = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id
    )
    return output['StandardOutputContent']

try:
    print("--- DOCKER STATUS ---")
    print(run_command("docker ps -a"))
    print("\n--- HYPEROPT LOGS ---")
    print(run_command("tail -n 100 Freqtrade/user_data/logs/freqtrade.log | grep -i 'epoch' || tail -n 20 Freqtrade/user_data/logs/freqtrade.log"))
except Exception as e:
    print(f"Error SSM: {e}")

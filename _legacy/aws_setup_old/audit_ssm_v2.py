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
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': [cmd]}
        )
        command_id = response['Command']['CommandId']
        
        # Esperar a que el comando termine (hasta 30s)
        for _ in range(6):
            time.sleep(5)
            output = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            if output['Status'] in ['Success', 'Failed', 'Cancelled']:
                return output['StandardOutputContent'] if output['StandardOutputContent'] else output['StandardErrorContent']
        return "Timeout esperando comando"
    except Exception as e:
        return f"Error: {e}"

print("--- EXPLORACIÓN DE RUTAS ---")
print(run_command("ls -R /home/ubuntu | grep Freqtrade | head -n 20"))
print("\n--- DOCKER REAL-TIME ---")
print(run_command("docker ps -a --format '{{.Names}} - {{.Status}}'"))
print("\n--- HYPEROPT STATUS ---")
print(run_command("find /home/ubuntu -name freqtrade.log -exec tail -n 20 {} +"))

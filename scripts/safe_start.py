import boto3, os, time
from dotenv import load_dotenv

load_dotenv('.env.aws')

AWS_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
INSTANCE_ID = os.getenv('AWS_INSTANCE_ID')
REGION = 'sa-east-1'

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

def wait_and_start():
    print(f"Esperando a que la instancia {INSTANCE_ID} se detenga...")
    while True:
        resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        state = resp['Reservations'][0]['Instances'][0]['State']['Name']
        if state == 'stopped':
            break
        print(f"Estado actual: {state}. Reintentando en 10s...")
        time.sleep(10)
    
    print("Limpiando tags...")
    ec2.delete_tags(Resources=[INSTANCE_ID], Tags=[{'Key': 'MODE'}])
    
    print("Iniciando instancia...")
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[INSTANCE_ID])
    
    resp = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    ip = resp['Reservations'][0]['Instances'][0].get('PublicIpAddress')
    print(f"SISTEMA EN LINEA. IP: {ip}")

if __name__ == "__main__":
    wait_and_start()

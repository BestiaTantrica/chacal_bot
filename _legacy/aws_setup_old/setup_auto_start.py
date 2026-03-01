import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv(".env.aws")

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

events = boto3.client('events', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

# Usaremos la misma Lambda chacal_bot_v2 pero le agregaremos una lógica para "encender"
# O mejor, crear una regla que llame directamente a una Lambda de sistema o a la nuestra con un evento especial.

def setup_eventbridge_rules():
    print("Configurando reglas de encendido automático...")
    
    # 1. Regla AM (07:50 UTC - Pre-Londres)
    rule_am = events.put_rule(
        Name="SniperV4_Start_AM",
        ScheduleExpression="cron(50 7 * * ? *)", # 07:50 UTC
        State='ENABLED',
        Description="Enciende Sniper V4 para la ventana AM (Londres)"
    )
    
    # 2. Regla PM (13:20 UTC - Pre-New York)
    rule_pm = events.put_rule(
        Name="SniperV4_Start_PM",
        ScheduleExpression="cron(20 13 * * ? *)", # 13:20 UTC
        State='ENABLED',
        Description="Enciende Sniper V4 para la ventana PM (New York)"
    )
    
    # Target: La Lambda chacal_bot_v2 con un payload que fuerce el encendido
    target_payload = {"action": "START_SERVER_AUTO"}
    
    events.put_targets(
        Rule="SniperV4_Start_AM",
        Targets=[{
            'Id': 'StartLambda',
            'Arn': f"arn:aws:lambda:{REGION}:{boto3.client('sts', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY).get_caller_identity()['Account']}:function:chacal_bot_v2",
            'Input': json.dumps(target_payload)
        }]
    )
    
    events.put_targets(
        Rule="SniperV4_Start_PM",
        Targets=[{
            'Id': 'StartLambda',
            'Arn': f"arn:aws:lambda:{REGION}:{boto3.client('sts', aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY).get_caller_identity()['Account']}:function:chacal_bot_v2",
            'Input': json.dumps(target_payload)
        }]
    )
    
    # Dar permiso a EventBridge para llamar a la Lambda
    try:
        lambda_client.add_permission(
            FunctionName="chacal_bot_v2",
            StatementId="EventBridgeStartPermission",
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_am['RuleArn']
        )
    except: pass
    
    print("Reglas configuradas exitosamente.")

if __name__ == "__main__":
    setup_eventbridge_rules()

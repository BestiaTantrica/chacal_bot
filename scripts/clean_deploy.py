import boto3
import os
import time
import zipfile
import json
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ChatID = os.getenv("TELEGRAM_CHAT_ID")
REGION = "sa-east-1"

apigw = boto3.client('apigatewayv2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
iam = boto3.client('iam', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

API_NAME = "chacal_bot_api"
FUNC_NAME = "chacal_bot_v2"
ROLE_NAME = "ChacalLambdaRole"

def cleanup_apis():
    print("Borrando APIs viejas...")
    resp = apigw.get_apis()
    for item in resp.get('Items', []):
        if item['Name'] == API_NAME:
            try:
                apigw.delete_api(ApiId=item['ApiId'])
                print(f"Borrada API: {item['ApiId']}")
            except Exception as e:
                print(f"Error borrando {item['ApiId']}: {e}")

def get_role_arn():
    return iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']

def deploy_lambda(role_arn):
    print("Redesplegando Lambda...")
    try:
        lambda_client.delete_function(FunctionName=FUNC_NAME)
        time.sleep(5)
    except: pass

    zip_output = "lambda.zip"
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write("scripts/lambda_chacal.py", "lambda_function.py")
    with open(zip_output, 'rb') as f: zipped_code = f.read()

    resp = lambda_client.create_function(
        FunctionName=FUNC_NAME,
        Runtime='python3.9',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zipped_code},
        Timeout=60,
        Environment={
            'Variables': {
                'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
                'INSTANCE_ID': INSTANCE_ID,
                'CHAT_ID': ChatID
            }
        }
    )
    return resp['FunctionArn']

def create_api(lambda_arn):
    print("Creando nueva API Gateway...")
    api = apigw.create_api(Name=API_NAME, ProtocolType='HTTP')
    api_id = api['ApiId']
    endpoint = api['ApiEndpoint']
    
    integration = apigw.create_integration(
        ApiId=api_id,
        IntegrationType='AWS_PROXY',
        IntegrationUri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
        PayloadFormatVersion='2.0'
    )
    
    apigw.create_route(
        ApiId=api_id,
        RouteKey='$default',
        Target=f"integrations/{integration['IntegrationId']}"
    )
    
    apigw.create_stage(ApiId=api_id, StageName='$default', AutoDeploy=True)
    
    lambda_client.add_permission(
        FunctionName=FUNC_NAME,
        StatementId='APIGatewayInvoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:{REGION}:{iam.get_user()['User']['Arn'].split(':')[4]}:{api_id}/*/*"
    )
    return endpoint

if __name__ == "__main__":
    cleanup_apis()
    role = get_role_arn()
    l_arn = deploy_lambda(role)
    url = create_api(l_arn)
    
    import requests
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url}")
    print(f"\nSISTEMA LISTO Y LIMPIO")
    print(f"URL: {url}")

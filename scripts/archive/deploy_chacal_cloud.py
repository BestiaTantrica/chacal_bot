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

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
iam = boto3.client('iam', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
apigw = boto3.client('apigatewayv2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

ROLE_NAME = "ChacalLambdaRole"
FUNC_NAME = "chacal_bot_v2"
API_NAME = "chacal_bot_api"

def create_role():
    try:
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        }
        resp = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
        time.sleep(5) 
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonEC2FullAccess")
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
        # AGREGAR PERMISOS SSM
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMFullAccess")
        print(f"Role IAM {ROLE_NAME} actualizado con SSM.")
        return resp['Role']['Arn']
    except Exception as e:
        if "EntityAlreadyExists" in str(e):
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMFullAccess")
            return iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
        print(f"Error Role: {e}")
        return None

def deploy_lambda(role_arn):
    try:
        lambda_client.delete_function(FunctionName=FUNC_NAME)
        time.sleep(5)
    except: pass

    zip_output = "lambda.zip"
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write("scripts/lambda_chacal.py", "lambda_function.py")
    with open(zip_output, 'rb') as f: zipped_code = f.read()

    try:
        resp = lambda_client.create_function(
            FunctionName=FUNC_NAME,
            Runtime='python3.12',
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
        print(f"Function {FUNC_NAME} creada.")
        return resp['FunctionArn']
    except Exception as e:
        print(f"Error creating function: {e}")
        return None

def deploy_api_gateway(lambda_arn):
    api = apigw.create_api(Name=API_NAME, ProtocolType='HTTP')
    api_id = api['ApiId']
    endpoint = api['ApiEndpoint']
    integration = apigw.create_integration(ApiId=api_id, IntegrationType='AWS_PROXY', IntegrationUri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations", PayloadFormatVersion='2.0')
    apigw.create_route(ApiId=api_id, RouteKey='$default', Target=f"integrations/{integration['IntegrationId']}")
    apigw.create_stage(ApiId=api_id, StageName='$default', AutoDeploy=True)
    
    try:
        lambda_client.add_permission(
            FunctionName=FUNC_NAME, StatementId='APIGatewayInvoke', Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com', SourceArn=f"arn:aws:execute-api:{REGION}:{iam.get_user()['User']['Arn'].split(':')[4]}:{api_id}/*/*"
        )
    except: pass
    return endpoint

if __name__ == "__main__":
    arn = create_role()
    if arn:
        time.sleep(5)
        l_arn = deploy_lambda(arn)
        if l_arn:
            url = deploy_api_gateway(l_arn)
            import requests
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url}")
            print(f"DONE. URL: {url}")
    if os.path.exists("lambda.zip"): os.remove("lambda.zip")

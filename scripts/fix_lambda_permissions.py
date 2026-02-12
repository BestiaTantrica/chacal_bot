import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

# Correct API ID from endpoint https://3v0a8ulsif.execute-api...
NEW_API_ID = "3v0a8ulsif" 

def add_permission():
    print(f"Granting invoke permission to API Gateway: {NEW_API_ID}")
    try:
        lambda_client.add_permission(
            FunctionName='chacal_bot_v2',
            StatementId=f'APIGatewayInvoke-{NEW_API_ID}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f"arn:aws:execute-api:{REGION}:742873382759:{NEW_API_ID}/*/*"
        )
        print("Permission added successfully.")
    except lambda_client.exceptions.ResourceConflictException:
        print("Permission already exists (or conflict).")
    except Exception as e:
        print(f"Error adding permission: {e}")

if __name__ == "__main__":
    add_permission()

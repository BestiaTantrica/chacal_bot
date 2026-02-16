import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

def check_policy():
    print("Checking Lambda Resource Policy...")
    try:
        resp = lambda_client.get_policy(FunctionName='chacal_bot_v2')
        policy = json.loads(resp['Policy'])
        print(json.dumps(policy, indent=2))
        
        # Check for API Gateway permission
        found = False
        for stmt in policy['Statement']:
            if stmt.get('Action') == 'lambda:InvokeFunction' and 'apigateway' in stmt.get('Principal', {}).get('Service', ''):
                print(f"\nSUCCESS: Found permission for API Gateway: {stmt['Sid']}")
                found = True
        
        if not found:
            print("\nWARNING: No API Gateway permission found!")
            
    except lambda_client.exceptions.ResourceNotFoundException:
         print("\nCRITICAL: No Resource Policy found! API Gateway cannot invoke this function.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    check_policy()

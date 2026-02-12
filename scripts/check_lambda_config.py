import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"

lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
logs_client = boto3.client('logs', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

def check_lambda_config():
    print("--- LAMBDA CONFIGURATION ---")
    try:
        resp = lambda_client.get_function_configuration(FunctionName='chacal_bot_v2')
        env_vars = resp.get('Environment', {}).get('Variables', {})
        print("Environment Variables:")
        for k, v in env_vars.items():
            # Mask sensitive data
            val = v[:5] + "..." if len(v) > 5 else v
            print(f"  {k}: {val}")
            
        if 'TELEGRAM_TOKEN' not in env_vars:
            print("CRITICAL: TELEGRAM_TOKEN missing!")
        if 'INSTANCE_ID' not in env_vars:
            print("CRITICAL: INSTANCE_ID missing!")
            
    except Exception as e:
        print(f"Error checking config: {e}")

def get_latest_error_logs():
    print("\n--- LATEST ERROR LOGS ---")
    try:
        log_group = '/aws/lambda/chacal_bot_v2'
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        for stream in streams['logStreams']:
            print(f"Stream: {stream['logStreamName']}")
            events = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream['logStreamName'],
                limit=10,
                startFromHead=False
            )
            for e in events['events']:
                if "Error" in e['message'] or "Exception" in e['message'] or "Traceback" in e['message']:
                    print(f"  ERROR: {e['message'].strip()}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error reading logs: {e}")

if __name__ == "__main__":
    check_lambda_config()
    get_latest_error_logs()

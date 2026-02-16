import boto3
import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
TOKEN = os.getenv('TELEGRAM_TOKEN')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = "sa-east-1"

def check_webhook():
    print("--- TELEGRAM WEBHOOK INFO ---")
    try:
        res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
        print(json.dumps(res, indent=2))
        return res.get('result', {})
    except Exception as e:
        print(f"Error checking webhook: {e}")
        return {}

def check_lambda_logs():
    print("\n--- CLOUDWATCH LOGS (LAST 15 MIN) ---")
    try:
        logs_client = boto3.client('logs', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
        log_group = '/aws/lambda/chacal_bot_v2'
        
        # Get latest stream
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print("No log streams found.")
            return

        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"Reading stream: {stream_name}")
        
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=20,
            startFromHead=False
        )
        
        for event in events['events']:
            print(f"[{datetime.fromtimestamp(event['timestamp']/1000)}] {event['message'].strip()}")
            
    except Exception as e:
        print(f"Error reading logs: {e}")

import json
if __name__ == "__main__":
    check_webhook()
    check_lambda_logs()

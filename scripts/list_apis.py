import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

client = boto3.client('apigatewayv2', region_name='sa-east-1')

def list_apis():
    resp = client.get_apis()
    print("APIs encontradas:")
    for item in resp.get('Items', []):
        print(f"Name: {item['Name']}, Id: {item['ApiId']}, Endpoint: {item['ApiEndpoint']}")

if __name__ == "__main__":
    list_apis()

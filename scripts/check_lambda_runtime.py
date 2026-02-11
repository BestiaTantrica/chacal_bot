import boto3
import os
from dotenv import load_dotenv

load_dotenv('c:/Freqtrade/.env.aws')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def scan_region(region_name):
    print(f"\n--- Escaneando Region: {region_name} ---")
    try:
        client = boto3.client(
            'lambda', 
            region_name=region_name,
            aws_access_key_id=AWS_ID,
            aws_secret_access_key=AWS_KEY
        )
        paginator = client.get_paginator('list_functions')
        found = False
        for page in paginator.paginate():
            for function in page['Functions']:
                if function['Runtime'] == 'python3.9':
                    print(f"ALERTA: {function['FunctionName']} usa {function['Runtime']}")
                    found = True
                else:
                    # Opcional: ver que otras funciones hay
                    print(f"Info: {function['FunctionName']} usa {function['Runtime']}")
        if not found:
            print("No se encontraron funciones con Python 3.9.")
    except Exception as e:
        print(f"Error en {region_name}: {e}")

if __name__ == "__main__":
    # Escaneamos las posibles regiones del usuario
    regions = ['us-east-1', 'sa-east-1']
    for r in regions:
        scan_region(r)

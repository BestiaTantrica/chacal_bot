import boto3
import os
import time
import json
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.aws")

AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
INSTANCE_ID = os.getenv("AWS_INSTANCE_ID")
REGION = "sa-east-1"

iam = boto3.client('iam', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)
ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)

EC2_ROLE_NAME = "ChacalEC2SSMRole"
EC2_PROFILE_NAME = "ChacalEC2SSMProfile"

def setup_ec2_ssm_role():
    print("Configurando Role para EC2 (SSM)...")
    try:
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        }
        iam.create_role(RoleName=EC2_ROLE_NAME, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
        iam.attach_role_policy(RoleName=EC2_ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")
    except Exception as e:
        if "EntityAlreadyExists" not in str(e): print(f"Error Role: {e}")

    try:
        iam.create_instance_profile(InstanceProfileName=EC2_PROFILE_NAME)
        time.sleep(2)
        iam.add_role_to_instance_profile(InstanceProfileName=EC2_PROFILE_NAME, RoleName=EC2_ROLE_NAME)
    except Exception as e:
        if "EntityAlreadyExists" not in str(e): print(f"Error Profile: {e}")

    # Asociar perfil a la instancia si no tiene uno
    try:
        time.sleep(5)
        ec2.associate_iam_instance_profile(
            IamInstanceProfile={'Name': EC2_PROFILE_NAME},
            InstanceId=INSTANCE_ID
        )
        print(f"Perfil SSM asociado a la instancia {INSTANCE_ID}.")
    except Exception as e:
        print(f"Info: {e} (Probablemente ya tiene uno)")

if __name__ == "__main__":
    setup_ec2_ssm_role()

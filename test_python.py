import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# STS client to verify identity
sts = boto3.client(
    "sts",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

print(sts.get_caller_identity())

# Bedrock client
client = boto3.client(
    "bedrock",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

response = client.list_inference_profiles()

for profile in response["inferenceProfileSummaries"]:
    print(profile["inferenceProfileName"])
    print(profile["inferenceProfileArn"])
    print("-------------------------")
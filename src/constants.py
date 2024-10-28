import os

REGION_NAME = "us-east-1"
LLM_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
INGEST_LLM_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"  # model to generate metadata per image
TEMPERATURE = 0
OS_INDEX_NAME = os.environ["INDEX_NAME"]
OS_HOST = os.environ["AOSS_URL"]
OS_PORT = os.environ["AOSS_PORT"]

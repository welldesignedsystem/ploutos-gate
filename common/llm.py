import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from langchain_aws import ChatBedrock

load_dotenv()


def _get_bedrock_config():
    return Config(
        connect_timeout=2,
        read_timeout=5,
        retries={"max_attempts": 1, "mode": "standard"},
    )


def build_llm():
    model_id = os.getenv("BEDROCK_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")
    try:
        client = boto3.client("bedrock-runtime", region_name=region, config=_get_bedrock_config())
    except Exception as e:
        raise RuntimeError(f"AWS Bedrock client init failed: {e}") from e
    return ChatBedrock(
        model_id=model_id,
        client=client,
        region_name=region,
        temperature=0,
        max_tokens=None,
    )

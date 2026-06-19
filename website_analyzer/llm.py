import os

from dotenv import load_dotenv
from langchain_aws import ChatBedrock

load_dotenv()


def build_llm():
    model_id = os.getenv("BEDROCK_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")
    return ChatBedrock(
        model_id=model_id,
        region_name=region,
        temperature=0,
        max_tokens=None,
    )

import json
import re
from typing import Any, cast

import httpx
from pydantic import BaseModel

from .models import LLMConfig

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


async def chat(
    system: str,
    user: str,
    config: LLMConfig | None = None,
) -> str | None:
    if config is None:
        config = LLMConfig.from_env()

    if config.provider != "anthropic" or not config.api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _ANTHROPIC_URL,
                headers={
                    "x-api-key": config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": config.model,
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            blocks = cast(list[dict[str, Any]], data.get("content", []))
            for block in blocks:
                if block.get("type") == "text":
                    return cast(str, block["text"])
            return None
    except Exception:
        return None


async def structured_chat(
    system: str,
    user: str,
    model_type: Any,
    config: LLMConfig | None = None,
) -> Any:
    is_list = getattr(model_type, "__origin__", None) is list
    inner_type: Any = getattr(model_type, "__args__", [None])[0] if is_list else model_type

    if is_list and inner_type and issubclass(inner_type, BaseModel):
        schema = {
            "type": "array",
            "items": inner_type.model_json_schema(),
        }
    else:
        schema = model_type.model_json_schema()

    system_prompt = (
        system + "\n\n"
        "You MUST respond with valid JSON only. "
        "Do NOT wrap the JSON in markdown code blocks. "
        f"Use this JSON schema:\n{json.dumps(schema, indent=2)}"
    )
    text = await chat(system_prompt, user, config)
    if not text:
        return None
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return None
    if is_list and inner_type and issubclass(inner_type, BaseModel):
        return [inner_type.model_validate(item) for item in data]
    return model_type.model_validate(data)

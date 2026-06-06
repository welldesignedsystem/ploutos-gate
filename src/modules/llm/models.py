import os
from pydantic import BaseModel


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        key_var = f"{provider.upper()}_API_KEY"
        return cls(
            provider=provider,
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-6"),
            api_key=os.getenv(key_var, ""),
        )

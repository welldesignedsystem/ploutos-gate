import os

from pydantic import BaseModel


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        key_var = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(key_var, "")

        if not api_key and provider == "anthropic":
            fallback_key = os.getenv("OPENROUTER_API_KEY", "")
            if fallback_key:
                return cls(
                    provider="openrouter",
                    model=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
                    api_key=fallback_key,
                )

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
        )

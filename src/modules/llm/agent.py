from collections.abc import Callable, Sequence
from typing import Any

from deepagents import create_deep_agent

from .models import LLMConfig


def create_agent(
    config: LLMConfig,
    tools: Sequence[Callable[..., str]],
    system_prompt: str = "",
) -> Any:
    model_str = f"{config.provider}:{config.model}"
    return create_deep_agent(
        model=model_str,
        tools=list(tools),
        system_prompt=system_prompt,
    )

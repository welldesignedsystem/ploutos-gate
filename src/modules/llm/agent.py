from collections.abc import Callable, Sequence

from deepagents import create_deep_agent

from .models import LLMConfig


def create_agent(
    config: LLMConfig,
    tools: Sequence[Callable],
    system_prompt: str = "",
) -> Callable:
    model_str = f"{config.provider}:{config.model}"
    return create_deep_agent(
        model=model_str,
        tools=tools,
        system_prompt=system_prompt,
    )

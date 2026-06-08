import os

from llm.models import LLMConfig


def test_from_env_defaults():
    os.environ.pop("LLM_PROVIDER", None)
    os.environ.pop("LLM_MODEL", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)

    cfg = LLMConfig.from_env()
    assert cfg.provider == "anthropic"
    assert cfg.model == "claude-sonnet-4-6"
    assert cfg.api_key == ""


def test_from_env_custom_provider():
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["LLM_MODEL"] = "gpt-4o"
    os.environ["OPENAI_API_KEY"] = "sk-test123"

    cfg = LLMConfig.from_env()
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4o"
    assert cfg.api_key == "sk-test123"


def test_from_env_picks_correct_key_var():
    os.environ["LLM_PROVIDER"] = "anthropic"
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
    os.environ.pop("OPENAI_API_KEY", None)

    cfg = LLMConfig.from_env()
    assert cfg.api_key == "sk-ant-test"

# ploutos-gate

Python 3.12, package `ploutos-gate` (hyphen). Sources under `src/modules/` — discoverable packages are `reddit*`, `llm*` (others planned: `seo*`, `aeo*`, `geo*`). Deps: `mcp`, `praw`, `python-dotenv`, `deepagents`, `langchain-anthropic`.

## Commands

```bash
# install (either works)
.venv/bin/pip3 install -e .
uv pip install -e .            # uv.lock present

# optional dev extras (pytest, ruff, mypy)
uv pip install -e ".[dev]"

# run MCP server (streamable-http on :8000)
.venv/bin/python -m reddit.server

# test (no test prefix needed, pytest auto-discovers)
.venv/bin/python -m pytest

# lint
.venv/bin/python -m ruff check .

# typecheck
.venv/bin/python -m mypy src/modules

# lint + format
.venv/bin/python -m ruff format --check .
```

## Toolchain quirks

- **Lint**: ruff, `line-length = 120`, `quote-style = "double"`, rules `E,F,I,N,W,UP,B,SIM`.
- **Typecheck**: mypy `strict = true`; ignores `praw.*`, `deepagents.*`, `mcp.*`.
- **Tests**: pytest + pytest-mock, no prefix/suffix convention. Test files live in `tests/`.

## Architecture

```
src/modules/
  reddit/
    server.py                — FastMCP, lazy RedditClient singleton
    client.py                — PRAW wrapper, 1 req/s throttle, subreddit filtering
    config.py                — RedditConfig (dataclass) from REDDIT_* env vars
    analyze/
      models.py              — Pydantic schemas for 8 analysis capabilities
      capabilities.py        — DeepAgent per capability calling RedditClient directly
      tools/register.py      — 8 analyzer_* MCP tools (the only MCP surface)
  llm/
    models.py                — LLMConfig: reads LLM_PROVIDER / LLM_MODEL / *_API_KEY
    agent.py                 — create_agent(config, tools, prompt) factory
```

Analysis flow: MCP tool → `run_analysis(capability, query, client)` → `LLMConfig.from_env()` → `create_agent(config, tools, prompt)` → agent calls `RedditClient` in-process → returns LLM output string.

## Key facts

- **.env must exist** with `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` + `ANTHROPIC_API_KEY`. Loaded automatically in `server.py` via `load_dotenv()`.
- **Reddit write tools** (`create_post`, `reply`) require `REDDIT_USERNAME` + `REDDIT_PASSWORD`.
- **LLM provider** swappable via `LLM_PROVIDER`; set the corresponding `*_API_KEY`. Default: `anthropic` / `claude-sonnet-4-6`.
- **Subreddit filtering**: `REDDIT_SUBREDDIT_ALLOWLIST` / `REDDIT_SUBREDDIT_BLOCKLIST`, comma-separated, case-insensitive. Blocklist takes priority.
- **Rate limit**: 1 Reddit API call/sec (`client.py:22-27`).
- **Limit clamping**: all tools clamp to 100 via `min(limit, 100)` in `_make_tools` + `le=100` in `AnalysisBase`.
- **Tool output**: formatted strings (not raw dicts).
- **Transport**: `streamable-http` (not default stdio), port 8000.
- **`reply` routing**: `len(parent_id) >= 6` → submission, else comment.
- **`track_mentions` param**: takes `list[str]` keywords (not comma-separated string).
- **`REDDIT_USER_AGENT`**: env-overridable, default `"ploutos-gate:1.0.0 (by /u/ploutos-gate-bot)"`.
- **No CI** configured.
- **`main.py` at root** is unused — entrypoint is `reddit.server`.

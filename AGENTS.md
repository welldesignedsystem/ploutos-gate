# ploutos-gate

Python 3.12 package. Dependencies: `mcp`, `praw`, `python-dotenv`, `deepagents`, `langchain-anthropic`.

## Install & verify

```bash
.venv/bin/python -m ensurepip          # one-time pip bootstrap
.venv/bin/pip3 install -e .
.venv/bin/python -c "from reddit.server import mcp; print('OK')"
```

`uv` also works (uv.lock present): `uv pip install -e .`

## Run MCP server (streamable-http on :8000)

```bash
.venv/bin/python -m reddit.server
```

Copy `.env.example` → `.env`, fill in `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `ANTHROPIC_API_KEY`. The server loads `.env` automatically.

## Architecture

```
src/modules/
  reddit/           — Reddit API data layer (PRAW)
    server.py       — FastMCP, lazy singleton RedditClient
    client.py       — PRAW wrapper, 1 req/s throttle, subreddit filtering
    config.py       — RedditConfig dataclass from REDDIT_* env vars
    analyze/        — AI analysis layer (Deep Agents)
      models.py       — Pydantic schemas for 8 analysis capabilities
      capabilities.py — Deep agent per capability, calls RedditClient directly
      tools/
        register.py   — 8 analyzer_* MCP tools (the only MCP surface)
  llm/              — Shared LLM provider abstraction
    models.py       — LLMConfig: provider-agnostic, reads LLM_PROVIDER / LLM_MODEL / *_API_KEY
    agent.py        — create_agent(config, tools, prompt) factory
```

### How analysis works

```
User → reddit.analyze MCP tool
  → deepagent (with capability-specific system prompt)
    → calls RedditClient methods directly (in-process)
    → LLM analyzes results
  → returns analysis string
```

## Key facts

- **Reddit write tools** require `REDDIT_USERNAME` + `REDDIT_PASSWORD`.
- **LLM provider** is swappable via `LLM_PROVIDER` env var — no code changes.
- **Subreddit filtering**: `REDDIT_SUBREDDIT_ALLOWLIST` / `REDDIT_SUBREDDIT_BLOCKLIST`, comma-separated, case-insensitive.
- **Rate limit**: 1 Reddit API call/sec (`client.py:22-27`).
- **Limit clamping**: all reddit tools cap at 100 (`min(limit, 100)`).
- **Tool output**: formatted strings, not raw dicts.
- **`track_mentions`**: comma-separated `keywords`, splits internally.
- **`reply`**: post vs comment by ID length (≥6 chars = submission).
- **Transport**: `streamable-http` (not default stdio).
- **No tests, CI, or linters** configured. No git history (all files untracked).

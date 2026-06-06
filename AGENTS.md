# ploutos-gate

Python 3.12 package. Dependencies: `mcp`, `praw`, `python-dotenv`.

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

Copy `.env.example` → `.env`, fill in `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`. The server loads `.env` automatically at startup via `load_dotenv()` in `server.py:1-4`.

## Architecture

```
src/modules/
  reddit/           — Python package, importable as `reddit.*`
    server.py       — FastMCP app, lazy singleton RedditClient
    client.py       — PRAW wrapper, 1 req/s throttle, subreddit filtering
    config.py       — RedditConfig dataclass from REDDIT_* env vars
    tools/          — tool registration, each file exports register_tools()
```

Tool registration: each `tools/*.py`'s `register_tools(mcp, get_client)` is called at import from `server.py:30-34`.

## Key facts

- **Write tools** require `REDDIT_USERNAME` + `REDDIT_PASSWORD` set.
- **Subreddit filtering**: `REDDIT_SUBREDDIT_ALLOWLIST` (if set, only those allowed) and `REDDIT_SUBREDDIT_BLOCKLIST`. Both comma-separated, case-insensitive.
- **Rate limit**: 1 API call/sec (`client.py:22-27`).
- **Limit clamping**: all tools cap at 100 (`min(limit, 100)`).
- **Tool output**: formatted strings, not raw dicts.
- **`track_mentions`**: takes comma-separated `keywords`, splits internally.
- **`reply`**: post vs comment by ID length (≥6 chars = submission).
- **Transport**: `streamable-http` (not default stdio).
- **No tests, CI, or linters** configured. No git history (all files untracked).

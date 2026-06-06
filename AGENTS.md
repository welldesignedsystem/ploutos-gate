# ploutos-gate

Python 3.12 package (`ploutos-gate` → namespace `ploutos_gate`). Dependencies: `mcp`, `praw`, `python-dotenv`.

## Install & verify

```bash
.venv/bin/python -m ensurepip          # one-time pip bootstrap
.venv/bin/pip3 install -e .
.venv/bin/python -c "from ploutos_gate.mcp.reddit.server import mcp; print('OK')"
```

## Run MCP server (HTTP+SSE on :8000)

```bash
.venv/bin/python -m ploutos_gate.mcp.reddit.server
```

Copy `.env.example` → `.env`, fill in `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`. The server loads `.env` automatically at startup (`server.py:3-5`).

## Architecture

```
ploutos_gate/
  mcp/reddit/
    server.py    — FastMCP app, lazy singleton RedditClient via _get_client()
    client.py    — PRAW wrapper, 1 req/s throttle, subreddit filtering
    config.py    — RedditConfig dataclass, from_env() reads REDDIT_* vars
    tools/
      search.py  → reddit_search_posts  (keyword search)
      browse.py  → reddit_get_post, reddit_read_subreddit
      info.py    → reddit_subreddit_info, reddit_user_info
      monitor.py → reddit_track_mentions
      write.py   → reddit_create_post, reddit_reply
```

Each `tools/*.py` exports `register_tools(mcp, get_client)` — called at import time in `server.py:25-29`.

## Key facts

- **Write tools** require `REDDIT_USERNAME` + `REDDIT_PASSWORD` set.
- **Subreddit filtering**: `REDDIT_SUBREDDIT_ALLOWLIST` (if set, only those allowed) and `REDDIT_SUBREDDIT_BLOCKLIST`. Both comma-separated, case-insensitive.
- **Rate limit**: 1 API call/sec enforced in `client.py:22-27`.
- **Limit clamping**: all tools cap at 100 (passed limit is `min(limit, 100)`).
- **Tool output**: all MCP tools return formatted strings, not raw dicts.
- **`track_mentions`**: takes comma-separated `keywords` string, splits internally.
- **`reply`**: distinguishes post vs comment by ID length (≥6 chars = submission).
- **No tests, CI, or linters** configured. No git history (all files untracked).

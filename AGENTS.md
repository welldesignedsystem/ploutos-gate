# ploutos-gate

Python 3.12. Sources under `src/modules/` import flat — use `from reddit.client import RedditClient`, NOT `from modules.reddit.client`.

## Commands

```bash
uv pip install -e ".[dev]"          # install + dev extras
uv run pytest                       # tests (auto-discovers, no prefix)
uv run ruff check .                 # lint
uv run mypy src/modules             # typecheck (strict)
uv run ruff format --check .        # format check (double quotes, 120 width)
uv run python -m reddit.server      # MCP server port 8000 (streamable-http)
uv run python -m rankprint.mcp_server   # MCP server port 8001 (streamable-http)
uv run uvicorn rankprint.api_server:app --port 8001  # FastAPI /api/scan + /health
```

## Packages

### reddit (port 8000, streamable-http)
- `server.py` — FastMCP, lazy `RedditClient` singleton, `load_dotenv()` at import time
- `client.py` — PRAW wrapper, 1 req/s throttle, subreddit allow/block filtering
- `config.py` — `RedditConfig` from `REDDIT_*` env vars; `is_subreddit_allowed()` blocklist-precedence
- `analyze/models.py` — Pydantic input schemas per capability; limit clamped `ge=1, le=100`
- `analyze/capabilities.py` — DeepAgent per capability; tools: `search_posts`, `get_post`, `read_subreddit`
- `analyze/tools/register.py` — 8 `analyzer_*` MCP tools (sole MCP surface), output = formatted strings

### llm
- `models.py` — `LLMConfig` reads `LLM_PROVIDER` / `LLM_MODEL` / `{PROVIDER}_API_KEY`
- `agent.py` — `create_agent(config, tools, prompt)` → `deepagents.create_deep_agent`
- `client.py` — async `chat()` (Anthropic direct API), `structured_chat()` for Pydantic-validated JSON output (also supports `list[BaseModel]`)

### rankprint (port 8001)
- `mcp_server.py` — FastMCP `rankprint_scan` tool, takes `url` + `terms[]` + `max_queries` (default 10) + `results_per_query` (default 10)
- `api_server.py` — FastAPI `POST /api/scan` + `GET /health`; no `__main__`, run via `uvicorn`
- `client.py` — orchestrator: fetch page text → extract `BusinessProfile` (LLM `structured_chat`) → generate up to `max_queries` search queries (LLM) → run each against all available providers → classify → `CompanyScanOutput`. Falls back to raw `terms` (truncated to `max_queries`) if LLM unavailable.
- `serp.py` — `DuckDuckGoChecker` (httpx POST to `html.duckduckgo.com/html/`, no API key, configurable delay via `RANKPRINT_SERP_DELAY` env var, default 3s), `TavilyChecker` (httpx POST to `api.tavily.com/search`, needs `TAVILY_API_KEY`, 1 req/s throttle)
- `models.py` — `ScanRequest(url, terms[], max_queries, results_per_query)` input, `CompanyScanOutput` output
- `crawler.py` — `fetch_page_text()` via httpx + bs4; strips script/style/nav/footer/header/aside; truncates at 10k chars

## Key facts

- `.env` must exist with `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` + `ANTHROPIC_API_KEY`
- `load_dotenv()` fires at import time in `reddit/server.py`, `rankprint/mcp_server.py`, and `rankprint/api_server.py`
- Write tools (`create_post`, `reply`) require `REDDIT_USERNAME` + `REDDIT_PASSWORD`
- `reply` routing: `len(parent_id) >= 6` → `praw.submission()`, else `praw.comment()`
- `track_mentions` takes `list[str]` keywords, not comma-separated string
- LLM provider swappable via `LLM_PROVIDER`; default `anthropic` / `claude-sonnet-4-6`
- Subreddit filters: `REDDIT_SUBREDDIT_ALLOWLIST` / `BLOCKLIST`, comma-separated, case-insensitive. Blocklist wins.
- `main.py` at root is unused. No CI configured.
- Package manifest includes [`reddit*`, `llm*`, `rankprint*`, `seo*`, `aeo*`, `geo*`] — only first three exist.
- rankprint `llm.client.structured_chat` currently only supports Anthropic (returns `None` for other providers).
- `.env.example` documents additional rankprint env vars (`TAVILY_API_KEY`, `SEARCH_PROVIDER`, etc.) not shown in README.
- Tests use standard pytest auto-discovery; async tests use `pytest.mark.asyncio`.

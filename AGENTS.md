# ploutos-gate

Python 3.12. Sources under `src/modules/` import flat — use `from reddit.client import RedditClient`, NOT `from modules.reddit.client`. Deps: `mcp`, `praw`, `python-dotenv`, `deepagents`, `langchain-anthropic`, `httpx`, `beautifulsoup4`, `lxml`, `fastapi`, `uvicorn`.

## Commands

```bash
uv pip install -e ".[dev]"          # install + dev extras
uv run pytest                       # tests (auto-discovers, no prefix)
uv run ruff check .                 # lint
uv run mypy src/modules             # typecheck (strict, ignores praw/deepagents/mcp)
uv run ruff format --check .        # format check (double quotes, 120 width)
uv run python -m reddit.server      # MCP server port 8000
uv run python -m rankprint.mcp_server  # MCP server port 8001
uv run python -m rankprint.api_server   # FastAPI port 8001 /api/scan
```

## Architecture

### reddit (port 8000, streamable-http)
- `server.py` — FastMCP, lazy `RedditClient` singleton, calls `load_dotenv()`
- `client.py` — PRAW wrapper, 1 req/s throttle, subreddit allow/block filtering
- `analyze/capabilities.py` — DeepAgent per capability, tools: search_posts, get_post, read_subreddit
- `analyze/tools/register.py` — 8 `analyzer_*` MCP tools (sole MCP surface), output = formatted strings
- Limit clamped to 100 (`min(limit, 100)` in capabilities, `le=100` in models)

### llm
- `models.py` — `LLMConfig` reads `LLM_PROVIDER` / `LLM_MODEL` / `{PROVIDER}_API_KEY`
- `agent.py` — `create_agent(config, tools, prompt)` → `deepagents.create_deep_agent`
- `client.py` — async `chat()` for simple LLM prompts, `structured_chat()` for Pydantic-validated JSON output (used by rankprint to extract profile + generate queries)

### rankprint (port 8001, streamable-http)
- `mcp_server.py` — `rankprint_scan` takes `url` + `terms[]`, returns JSON. Uses `ToolAnnotations(readOnlyHint=True)`.
- `api_server.py` — FastAPI `POST /api/scan` + `GET /health`
- `client.py` — orchestrator: scrape → extract `BusinessProfile` (LLM structured) → generate relevant SERP queries (LLM structured) → search DuckDuckGo → classify results → return `CompanyScanOutput`. Falls back to raw user `terms` if LLM unavailable.
- `serp.py` — `DuckDuckGoChecker` (active); `BingChecker`/`GoogleCSEChecker`/`TavilyChecker` (defined but unwired)
- `models.py` — `ScanRequest(url, terms[])` input, `BusinessProfile` (extracted via LLM), `GeneratedSearchQuery` (with intent+reason), `CompanyScanOutput` output; legacy `RankprintOutput` schemas
- `aggregator.py`, `crawler.py`, `keyword_gen.py`, `business.py`, `query_gen.py` — **unused/dead code**, not imported by `client.py`
- `README.md` is **aspirational** — describes planned Node.js infrastructure not present in this Python codebase

## Key facts

- `.env` must exist with `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` + `ANTHROPIC_API_KEY`. Loaded by `load_dotenv()` in each server entrypoint.
- Write tools (`create_post`, `reply`) require `REDDIT_USERNAME` + `REDDIT_PASSWORD`.
- `reply` routing: `len(parent_id) >= 6` → submission, else comment.
- `track_mentions` takes `list[str]` keywords, not comma-separated string.
- LLM provider swappable via `LLM_PROVIDER`; default `anthropic` / `claude-sonnet-4-6`.
- Subreddit filters: `REDDIT_SUBREDDIT_ALLOWLIST` / `BLOCKLIST`, comma-separated, case-insensitive. Blocklist wins.
- `main.py` at root is unused. No CI configured.
- Rankprint: DuckDuckGo-only (no API keys needed), 3s delay between requests (`RANKPRINT_SERP_DELAY`). Input: `url` + `terms[]` (list[str]).

# ploutos-gate

Python 3.12. Sources under `src/modules/` import flat — use `from probe.client import probe`, NOT `from modules.probe.client`.

## Commands

```bash
uv pip install -e ".[dev]"          # install + dev extras
uv run pytest                       # tests (auto-discovers, no prefix)
uv run ruff check .                 # lint
uv run mypy src/modules             # typecheck (strict)
uv run ruff format --check .        # format check (double quotes, 120 width)
./probe                                 # probe API server port 8003 (default)
./probe mcp                             # probe MCP server port 8002
uv run python -m probe.mcp_server       # MCP server port 8002 (streamable-http)
uv run uvicorn probe.api_server:app --port 8003  # FastAPI /api/probe + /health
```

## Packages

### llm
- `models.py` — `LLMConfig` reads `LLM_PROVIDER` / `LLM_MODEL` / `{PROVIDER}_API_KEY`
- `agent.py` — `create_agent(config, tools, prompt)` → `deepagents.create_deep_agent`
- `client.py` — async `chat()` (Anthropic direct API), `structured_chat()` for Pydantic-validated JSON output (also supports `list[BaseModel]`)

### probe (port 8002 MCP, port 8003 HTTP)
- `mcp_server.py` — FastMCP `probe_scan` tool, takes `url` + `max_terms` (default 20)
- `api_server.py` — FastAPI `POST /api/probe` + `GET /health`; no `__main__`, run via `uvicorn`
- `client.py` — `probe()`: fetch page text → extract `BusinessProfile` → generate competitor-finding terms via LLM → `ProbeOutput`. Each term includes LLM justification for why it was chosen. Falls back to company name if LLM unavailable.
- `models.py` — `ProbeRequest(url, max_terms)` input, `ProbeOutput(url, max_terms, target, terms[])` output
- `crawler.py` — `fetch_page_text()` via httpx + bs4; strips script/style/nav/footer/header/aside; truncates at 10k chars

## Key facts

- `.env` must exist with `ANTHROPIC_API_KEY` (or the key for your `LLM_PROVIDER`)
- `load_dotenv()` fires at import time in `probe/mcp_server.py` and `probe/api_server.py`
- LLM provider swappable via `LLM_PROVIDER`; default `anthropic` / `claude-sonnet-4-6`
- `main.py` at root is unused. No CI configured.
- `.env.example` documents additional rankprint env vars (`TAVILY_API_KEY`, `SEARCH_PROVIDER`, etc.) not shown in README.
- Tests use standard pytest auto-discovery; async tests use `pytest.mark.asyncio`.

# ploutos-gate

Utility libraries for **S**earch **E**ngine **O**ptimization (SEO),
**A**nswer **E**ngine **O**ptimization (AEO), and
**G**enerative **E**ngine **O**ptimization (GEO).

Company URL visibility scanning via search engine results.

## Getting started

```bash
uv pip install -e ".[dev]"
```

Copy `.env.example` → `.env` and fill in `ANTHROPIC_API_KEY`.

```bash
uv run uvicorn rankprint.api_server:app --port 8001
```

Serves `POST /api/scan` and `GET /health` on `http://localhost:8001`.

## Architecture

```
src/modules/
  rankprint/
    client.py          — orchestrator: crawl → profile → query → search → classify
    models.py          — ScanRequest, CompanyScanOutput, BusinessProfile, etc.
    serp.py            — DuckDuckGoChecker, TavilyChecker
    crawler.py         — fetch_page_text() via httpx + bs4
    mcp_server.py      — FastMCP server, rankprint_scan tool
    api_server.py      — FastAPI app, /api/scan + /health
  llm/
    models.py          — LLMConfig: provider-agnostic (reads env)
    client.py          — async chat() + structured_chat() (Anthropic direct API)
```

The `scan()` function fetches page text, extracts a `BusinessProfile` via LLM, generates search queries, runs them against DuckDuckGo (and Tavily if configured), and returns a `CompanyScanOutput` with ranked visibility results.

## API

### `POST /api/scan`

```json
{
  "url": "https://example.com",
  "terms": ["seed term"],
  "max_queries": 10,
  "results_per_query": 10
}
```

### `GET /health`

```json
{"status": "ok"}
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | No | "anthropic" | LLM provider (anthropic, openai, etc.) |
| `LLM_MODEL` | No | "claude-sonnet-4-6" | Model name |
| `ANTHROPIC_API_KEY` | See note | — | Required when LLM_PROVIDER=anthropic |
| `TAVILY_API_KEY` | No | — | Enables Tavily search provider |
| `RANKPRINT_SERP_DELAY` | No | 3 | Seconds between DuckDuckGo requests |

To switch providers, change `LLM_PROVIDER`, set the corresponding `*_API_KEY`, and install the matching `langchain-*` package. No code changes needed.

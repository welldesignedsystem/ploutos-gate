# rankprint

Rankprint measures whether a company appears in search results for the queries that matter to its business. Takes a URL, extracts a business profile via LLM, generates up to N search queries, runs them against all available providers, and returns ranked visibility results. If you don't provide seed terms, the AI derives them from the website content.

## Usage

```python
from rankprint.client import scan

result = await scan(
    "https://example.com",
    terms=["ai receptionist", "medical scheduling"],
    max_queries=10,
    results_per_query=10,
)

# terms are optional — AI generates queries by understanding the website:
result = await scan("https://example.com")
```

### MCP

```bash
uv run python -m rankprint.mcp_server
# tool: rankprint_scan(url, terms?=[], max_queries=10, results_per_query=10)
```

### FastAPI

```bash
uv run python -m rankprint.api_server
# POST /api/scan  { "url": "...", "terms?": [], "max_queries": 10, "results_per_query": 10 }
# GET  /health
```

## Input

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | URL | — | Company, product, or website to evaluate. |
| `terms` | `list[str]` | `[]` | Seed topics. If empty, AI generates queries by understanding the website. |
| `max_queries` | int | 10 | Number of search queries to generate (1–25). |
| `results_per_query` | int | 10 | Results to return per query per provider (1–50). |

## Flow

1. **Crawl** — fetch page text, strip script/style/nav/footer, truncate at 10k chars.
2. **Extract** — LLM (`structured_chat`) extracts `BusinessProfile` from page text.
3. **Generate** — LLM generates up to `max_queries` relevant search queries with intent + surface.
4. **Fallback** — if LLM unavailable, raw `terms` are used as queries (truncated to `max_queries`). If `terms` is also empty, falls back to company name or domain.
5. **Search** — each query is run against every available provider.
6. **Classify** — results are split into `matches` (target domain found) and `competitors` (everything else).

## Providers

| Provider | Env var | Key required |
|---|---|---|
| DuckDuckGo | — | No; always available |
| Tavily | `TAVILY_API_KEY` | Yes; skipped in `skipped_providers` if missing |

Missing-key providers are recorded in `skipped_providers` in the output.

## Output

`CompanyScanOutput` JSON with `company`, `query_results` (per query, per provider), `skipped_providers`, and `summary` (visibility score, best rank, etc.).

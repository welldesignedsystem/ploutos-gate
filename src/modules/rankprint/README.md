# rankprint

Rankprint measures whether a company appears in search, answer, and generative
engine results for the queries that matter to its business.

The module takes a company URL and user-provided seed terms, uses the LLM layer
to generate the most relevant search prompts, runs the prompts against available
providers, and returns ranked results with evidence text.

Providers that do not have API keys configured are skipped.

## Input

The first implementation should keep the public input small and stable:

```json
{
  "url": "https://example.com",
  "terms": ["ai receptionist", "phone answering service", "medical scheduling software"]
}
```

| Field | Type | Required | Description |
|---|---:|---:|---|
| `url` | URL | Yes | Company, product, or website to evaluate. |
| `terms` | `list[str]` | Yes | Seed topics, services, products, or keywords. |

Suggested Pydantic model:

```python
from pydantic import BaseModel, Field, HttpUrl


class ScanRequest(BaseModel):
    url: HttpUrl
    terms: list[str] = Field(min_length=1, max_length=25)
```

Optional v2 fields:

```json
{
  "url": "https://example.com",
  "terms": ["ai receptionist"],
  "max_queries": 10,
  "results_per_query": 10,
  "country": "us",
  "language": "en"
}
```

## Query Generation

After receiving input, Rankprint should:

1. Fetch and parse the target URL.
2. Extract a `BusinessProfile` from page text.
3. Ask the LLM to generate the most relevant search, answer, and generative
   engine prompts for the business and seed terms.
4. Fall back to the raw `terms` if the LLM provider or API key is unavailable.

Generated queries should include why the query matters:

```json
{
  "query": "best ai receptionist for medical clinics",
  "intent": "commercial",
  "surface": "seo",
  "reason": "The company appears to sell AI phone answering for healthcare teams."
}
```

## Providers

Rankprint should run each generated query against every configured provider it
supports. Results are grouped by query, then by provider, so evidence and
rankings are always interpreted in the context of the exact query that produced
them.

Initial provider groups:

| Group | Provider | Key behavior |
|---|---|---|
| SEO | DuckDuckGo | No key required; default fallback search provider. |
| SEO | Google Custom Search | Use only when `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ID` exist. |
| SEO | Bing Web Search | Use only when `BING_SEARCH_API_KEY` exists. |
| AEO | Perplexity | Use only when `PERPLEXITY_API_KEY` exists. |
| GEO | OpenAI / ChatGPT-style answer | Use only when `OPENAI_API_KEY` exists. |
| GEO | Anthropic / Claude-style answer | Use only when `ANTHROPIC_API_KEY` exists. |

If a provider key is missing, skip that provider and record it in
`skipped_providers`.

## Output

Output should be JSON-first and identical for MCP and FastAPI.

Every result must include evidence text relevant to the query. For classic
search engines, evidence comes from title, snippet, and optionally fetched page
text. For answer/generative engines, evidence comes from the answer text and
citations when available.

```json
{
  "company": {
    "url": "https://example.com",
    "domain": "example.com",
    "name": "Example",
    "description": "AI receptionist and scheduling software for clinics."
  },
  "query_results": [
    {
      "query": "best ai receptionist for medical clinics",
      "intent": "commercial",
      "surface": "seo",
      "reason": "The company appears to sell AI phone answering for healthcare teams.",
      "provider_results": [
        {
          "provider": "duckduckgo",
          "surface": "seo",
          "found": true,
          "best_rank": 4,
          "matches": [
            {
              "rank": 4,
              "title": "Example AI Receptionist",
              "url": "https://example.com",
              "domain": "example.com",
              "text_reference": {
                "source": "snippet",
                "text": "Example provides AI receptionist software for medical practices...",
                "relevance": "Mentions the target company and the medical clinic use case for this query."
              }
            }
          ],
          "competitors": [
            {
              "rank": 1,
              "title": "Competitor AI Receptionist",
              "url": "https://competitor.com",
              "domain": "competitor.com",
              "text_reference": {
                "source": "snippet",
                "text": "Compare AI receptionist tools for clinics and healthcare teams...",
                "relevance": "Ranks ahead of the target company for this commercial-intent query."
              }
            }
          ],
          "raw_answer": null,
          "citations": []
        },
        {
          "provider": "anthropic",
          "surface": "geo",
          "found": false,
          "best_rank": null,
          "matches": [],
          "competitors": [],
          "raw_answer": "Several AI receptionist tools for clinics include...",
          "citations": [],
          "text_reference": {
            "source": "answer",
            "text": "Several AI receptionist tools for clinics include...",
            "relevance": "The answer discusses this query topic but does not mention the target company."
          }
        }
      ]
    }
  ],
  "skipped_providers": [
    {
      "provider": "google_cse",
      "reason": "Missing GOOGLE_CSE_API_KEY or GOOGLE_CSE_ID."
    }
  ],
  "summary": {
    "queries_generated": 10,
    "providers_run": 3,
    "providers_skipped": 2,
    "total_checks": 30,
    "checks_found": 7,
    "best_rank": 2,
    "average_best_rank": 6.7,
    "visibility_score": 42
  }
}
```

## Suggested Models

```python
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


SearchSurface = Literal["seo", "aeo", "geo"]


class BusinessProfile(BaseModel):
    url: HttpUrl
    domain: str
    name: str | None = None
    description: str | None = None
    products: list[str] = Field(default_factory=list)
    audiences: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class GeneratedSearchQuery(BaseModel):
    query: str
    intent: Literal["informational", "commercial", "transactional", "navigational"]
    surface: SearchSurface
    reason: str


class TextReference(BaseModel):
    source: Literal["title", "snippet", "page", "answer", "citation"]
    text: str
    relevance: str


class RankedReference(BaseModel):
    rank: int | None = None
    title: str | None = None
    url: HttpUrl | None = None
    domain: str | None = None
    text_reference: TextReference


class ProviderResult(BaseModel):
    provider: str
    surface: SearchSurface
    found: bool
    best_rank: int | None = None
    matches: list[RankedReference] = Field(default_factory=list)
    competitors: list[RankedReference] = Field(default_factory=list)
    raw_answer: str | None = None
    citations: list[HttpUrl] = Field(default_factory=list)
    text_reference: TextReference | None = None


class QueryResult(GeneratedSearchQuery):
    provider_results: list[ProviderResult] = Field(default_factory=list)


class SkippedProvider(BaseModel):
    provider: str
    reason: str


class ScanSummary(BaseModel):
    queries_generated: int
    providers_run: int
    providers_skipped: int
    total_checks: int
    checks_found: int
    best_rank: int | None = None
    average_best_rank: float | None = None
    visibility_score: int


class CompanyScanOutput(BaseModel):
    company: BusinessProfile
    query_results: list[QueryResult]
    skipped_providers: list[SkippedProvider]
    summary: ScanSummary
```

## Implementation Order

1. Add `rankprint*` to package discovery.
2. Add the Pydantic models above.
3. Add URL fetching and page text extraction.
4. Add LLM-based business profile and query generation using
   `llm.client.structured_chat`.
5. Add provider interfaces with a shared result format.
6. Implement DuckDuckGo first because it requires no key.
7. Add keyed providers one at a time; skip any provider with missing env vars.
8. Add the scanner orchestrator.
9. Add MCP and FastAPI entrypoints that return the same `CompanyScanOutput`.
10. Add tests for validation, provider skipping, domain matching, references,
    and fallback behavior.

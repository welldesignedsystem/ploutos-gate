# ploutos-gate

Utility libraries for **S**earch **E**ngine **O**ptimization (SEO),
**A**nswer **E**ngine **O**ptimization (AEO), and
**G**enerative **E**ngine **O**ptimization (GEO).

Reddit-powered content research and competitive analysis via LLM agents.

## Getting started

```bash
.venv/bin/python -m ensurepip
.venv/bin/pip install -e .
```

Copy `.env.example` → `.env` and fill in `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `ANTHROPIC_API_KEY`.

```bash
.venv/bin/python -m reddit.server
```

Serves MCP tools on `http://localhost:8000` with `streamable-http` transport.

## Architecture

```
src/modules/
  reddit/
    client.py          — PRAW wrapper, internal data layer
    config.py          — RedditConfig from REDDIT_* env vars
    analyze/models.py       — Pydantic input schemas per capability
    analyze/capabilities.py — DeepAgent per capability calling RedditClient directly
    analyze/tools/register.py  — 8 analyzer_* MCP tools (the MCP surface)
    server.py          — FastMCP server, registers analyze tools
  llm/
    models.py          — LLMConfig: provider-agnostic (reads env)
    agent.py           — create_agent(config, tools, prompt) factory
```

Each `analyzer_*` MCP tool creates a LangChain DeepAgent with a capability-specific system prompt and direct access to `RedditClient` methods. The LLM provider is swappable via `LLM_PROVIDER` env var — no code changes.

## Capabilities

### `analyzer_keyword_discovery`
Mine Reddit for natural-language queries and long-tail keyword opportunities. Extracts exact phrases real users search for, question formats ("how to X", "why does Y", "best Z for"), niche terminology, and subreddit-specific jargon that traditional keyword tools miss.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | — | Topic to discover keywords for |
| `max_keywords` | integer | 20 | Max keywords to return |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_intent_analysis`
Classify why people search for a given query. Reads posts and top comments, then categorizes each by search intent — informational, commercial, transactional, or navigational. Identifies pain points, comparison requests, and tutorial needs to align content strategy with genuine user intent.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | — | Search query to analyze intent for |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_content_gaps`
Find frequently asked questions with no good answers. Identifies posts where the top answers are weak, outdated, or point to low-quality sources. Flags repeated questions with no definitive answer — each content gap includes the question, why existing answers are insufficient, and estimated search demand.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | — | Topic to find content gaps in |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_trend_detection`
Detect rising topics in a subreddit before they peak on Google Trends. Compares hot/rising posts against recent top posts, identifies momentum shifts in how the community frames a topic, and returns ranked trends with urgency level (act now / watch / monitor).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `subreddit` | string | — | Subreddit to detect trends in |
| `lookback_days` | integer | 7 | Days to look back |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_competitor_research`
Surface which domains get cited on Reddit for a given topic. Catalogs cited domains, citation context (recommended, mentioned in passing, criticized), and which aspects of the topic each domain owns. A proxy for domain authority and topical trust in a given niche.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | — | Topic to research competitors for |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_backlink_prospecting`
Find organic link placement opportunities by analyzing where Redditors link externally. For each linked page records domain, URL, anchor context, and post score. Identifies patterns — "if they linked to X here, they'd link to similar Y" — and flags orphan topics where people ask for resources but nobody links.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | — | Topic to find backlink opportunities in |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_serp_targeting`
Model what Google rewards in ranking Reddit threads. Analyzes highest-ranked threads — title structure, formatting, engagement patterns, and content format (lists, comparisons, detailed guides). Returns a template of SERP-winning thread characteristics for a given query space.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | — | Query to analyze SERP patterns for |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

### `analyzer_audience_language`
Extract exact words and phrases real users use when describing problems. Collects phrasing from posts, categorizes by sentiment (frustrated, curious, comparing, recommending), and groups by use case: headlines, meta descriptions, FAQ sections. Feed the output directly into on-page copy to improve semantic relevance without keyword stuffing.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | — | Topic to extract audience language for |
| `subreddits` | string | "all" | Comma-separated subreddit names |
| `time_filter` | string | "month" | hour, day, week, month, year, all |
| `limit` | integer | 50 | Max posts to analyze |

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDDIT_CLIENT_ID` | Yes | — | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | Yes | — | Reddit API client secret |
| `REDDIT_USERNAME` | No | — | For write operations (future use) |
| `REDDIT_PASSWORD` | No | — | For write operations (future use) |
| `REDDIT_SUBREDDIT_ALLOWLIST` | No | — | Restrict to these subreddits (comma-separated) |
| `REDDIT_SUBREDDIT_BLOCKLIST` | No | — | Exclude these subreddits (comma-separated) |
| `LLM_PROVIDER` | No | "anthropic" | LLM provider (anthropic, openai, ollama, etc.) |
| `LLM_MODEL` | No | "claude-sonnet-4-6" | Model name |
| `ANTHROPIC_API_KEY` | See note | — | Required when LLM_PROVIDER=anthropic |
| `OPENAI_API_KEY` | See note | — | Required when LLM_PROVIDER=openai |

To switch providers, change `LLM_PROVIDER`, set the corresponding `*_API_KEY`, and install the matching `langchain-*` package (e.g. `langchain-openai`). No code changes needed.
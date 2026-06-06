from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..capabilities import run_analysis
from ..models import (
    AudienceLanguage,
    BacklinkProspecting,
    CompetitorResearch,
    ContentGapAnalysis,
    IntentAnalysis,
    KeywordDiscovery,
    SERPTargeting,
    TrendDetection,
)


def register_tools(mcp: FastMCP, get_client: Callable) -> None:
    @mcp.tool(
        name="analyzer_keyword_discovery",
        description=(
            "Mine Reddit for natural-language queries and long-tail keyword "
            "opportunities around a given topic."
        ),
    )
    def keyword_discovery(params: KeywordDiscovery) -> str:
        return run_analysis(
            "keyword_discovery",
            f"Discover keywords for topic: {params.topic}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}. "
            f"Return up to {params.max_keywords} keywords.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_intent_analysis",
        description=(
            "Classify why people search for a query — informational, commercial, "
            "transactional, or navigational intent."
        ),
    )
    def intent_analysis(params: IntentAnalysis) -> str:
        return run_analysis(
            "intent_analysis",
            f"Analyze search intent for: {params.query}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_content_gaps",
        description=(
            "Find frequently asked questions with no good answers — "
            "content gaps worth targeting."
        ),
    )
    def content_gaps(params: ContentGapAnalysis) -> str:
        return run_analysis(
            "content_gaps",
            f"Find content gaps for topic: {params.topic}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_trend_detection",
        description=(
            "Detect rising topics in a subreddit before they peak on Google Trends."
        ),
    )
    def trend_detection(params: TrendDetection) -> str:
        return run_analysis(
            "trend_detection",
            f"Detect trends in r/{params.subreddit}. "
            f"Looking back {params.lookback_days} days. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_competitor_research",
        description=(
            "Surface which domains get cited on Reddit for a given topic — "
            "a proxy for topical authority."
        ),
    )
    def competitor_research(params: CompetitorResearch) -> str:
        return run_analysis(
            "competitor_research",
            f"Research competitors for topic: {params.topic}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_backlink_prospecting",
        description=(
            "Find organic link placement opportunities by analyzing where "
            "Redditors link externally."
        ),
    )
    def backlink_prospecting(params: BacklinkProspecting) -> str:
        return run_analysis(
            "backlink_prospecting",
            f"Find backlink opportunities for topic: {params.topic}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_serp_targeting",
        description=(
            "Model what Google rewards in ranking Reddit threads — "
            "title patterns, structure, engagement signals."
        ),
    )
    def serp_targeting(params: SERPTargeting) -> str:
        return run_analysis(
            "serp_targeting",
            f"Analyze SERP targeting for query: {params.query}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

    @mcp.tool(
        name="analyzer_audience_language",
        description=(
            "Extract exact words and phrases real users use when describing "
            "problems — for on-page copy and semantic relevance."
        ),
    )
    def audience_language(params: AudienceLanguage) -> str:
        return run_analysis(
            "audience_language",
            f"Extract audience language for topic: {params.topic}. "
            f"Search across: {params.subreddits}. "
            f"Time filter: {params.time_filter}.",
            get_client(),
        )

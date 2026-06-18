from collections.abc import Callable

from llm.agent import create_agent
from llm.models import LLMConfig

from ..client import RedditClient

_KEYWORD_PROMPT = (
    "You are an SEO keyword researcher. Your job is to mine Reddit for natural-language queries "
    "and long-tail keyword opportunities.\n\n"
    "Using the Reddit tools available to you:\n"
    "1. Search for posts about the given topic across specified subreddits\n"
    "2. Read post titles and selftext to extract exact phrases real users searched for\n"
    '3. Identify question formats ("how to X", "why does Y", "best Z for")\n'
    "4. Spot niche terminology and subreddit-specific jargon\n"
    "5. Return the keywords grouped by search intent with frequency estimates\n\n"
    "Focus on phrases that actual keyword tools would miss."
)

_INTENT_PROMPT = (
    "You are a search intent analyst. Your job is to classify why people search for specific things on Reddit.\n\n"
    "Using the Reddit tools:\n"
    "1. Search for the query across subreddits\n"
    "2. Read posts and top comments\n"
    "3. Classify each post's intent: informational, commercial, transactional, navigational\n"
    "4. Identify pain points, comparison requests, and tutorial needs\n"
    "5. Return a breakdown of intent categories with post examples\n\n"
    "This helps align content strategy with genuine user intent."
)

_CONTENT_GAP_PROMPT = (
    "You are a content strategist identifying content gaps on Reddit.\n\n"
    "Using the Reddit tools:\n"
    "1. Search for frequently asked questions about the topic\n"
    "2. Identify posts where the top answers are weak, outdated, or point to low-quality sources\n"
    "3. Look for the same question asked repeatedly with no definitive answer\n"
    "4. Flag each gap with: the question, why existing answers are insufficient, and estimated search volume\n\n"
    "These are opportunities for authoritative content."
)

_TREND_PROMPT = (
    "You are a trend spotter monitoring Reddit for emerging topics.\n\n"
    "Using the Reddit tools:\n"
    "1. Browse the subreddit's hot and rising posts\n"
    "2. Compare with top posts from the previous period\n"
    "3. Identify topics gaining momentum before they peak on Google Trends\n"
    "4. Note the language pattern shift — how is the community framing the topic?\n"
    "5. Return ranked trends with urgency level (act now / watch / monitor)\n\n"
    "Early detection gives a content advantage before saturation."
)

_COMPETITOR_PROMPT = (
    "You are a competitive researcher analyzing domain authority signals on Reddit.\n\n"
    "Using the Reddit tools:\n"
    "1. Search for the topic and collect posts mentioning external links\n"
    "2. Catalog which domains get cited for which aspects of the topic\n"
    "3. Note citation context — recommended as source, mentioned in passing, or criticized\n"
    "4. Identify domains that appear repeatedly for the same subtopics\n\n"
    "Return a competitive landscape: which domains own which topical clusters."
)

_BACKLINK_PROMPT = (
    "You are a link prospector finding backlink opportunities on Reddit.\n\n"
    "Using the Reddit tools:\n"
    "1. Search for external links in posts and comments about the topic\n"
    "2. For each linked page, note: domain, URL, anchor context, post score\n"
    '3. Identify patterns — "if they linked to X here, they\'d link to similar Y"\n'
    "4. Flag orphan topics where people ask for resources but no one links\n\n"
    "Return a list of link placement opportunities with rationale."
)

_SERP_PROMPT = (
    "You are a SERP analyst modeling what Google rewards in Reddit threads.\n\n"
    "Using the Reddit tools:\n"
    '1. Search for the query — focus on "best X" and "X Reddit" patterns\n'
    "2. Analyze the highest-ranked threads: title structure, formatting, engagement\n"
    "3. Identify common patterns: list posts, comparison tables, detailed guides\n"
    "4. Note what Google seems to reward: comment count? post age? formatting?\n\n"
    "Return a template of SERP-winning thread characteristics for this query space."
)

_AUDIENCE_PROMPT = (
    "You are an audience language modeler extracting exact user phrasing from Reddit.\n\n"
    "Using the Reddit tools:\n"
    "1. Search for posts about the topic\n"
    "2. Collect exact phrases users use when describing their problems\n"
    "3. Categorize by sentiment: frustrated, curious, comparing, recommending\n"
    "4. Identify recurring vocabulary and framing patterns\n"
    "5. Return the phrases grouped by use case: headlines, meta descriptions, FAQ sections\n\n"
    "Use these exact words to improve semantic relevance without keyword stuffing."
)

PROMPTS = {
    "keyword_discovery": _KEYWORD_PROMPT,
    "intent_analysis": _INTENT_PROMPT,
    "content_gaps": _CONTENT_GAP_PROMPT,
    "trend_detection": _TREND_PROMPT,
    "competitor_research": _COMPETITOR_PROMPT,
    "backlink_prospecting": _BACKLINK_PROMPT,
    "serp_targeting": _SERP_PROMPT,
    "audience_language": _AUDIENCE_PROMPT,
}


def _make_tools(client: RedditClient) -> list[Callable[..., str]]:
    def search_posts(
        query: str,
        subreddit: str | None = None,
        sort: str = "relevance",
        limit: int = 10,
        time_filter: str = "all",
    ) -> str:
        """Search Reddit posts by keyword across all subreddits or within a specific subreddit."""
        return str(client.search_posts(query, subreddit, sort, min(limit, 100), time_filter))

    def get_post(post_id: str) -> str:
        """Fetch a Reddit post by ID including its top-level comments."""
        return str(client.get_post(post_id))

    def read_subreddit(
        subreddit: str,
        sort: str = "hot",
        limit: int = 25,
        time_filter: str | None = None,
    ) -> str:
        """Browse a subreddit by hot, new, top, or rising posts."""
        return str(client.read_subreddit(subreddit, sort, min(limit, 100), time_filter))

    return [search_posts, get_post, read_subreddit]


def run_analysis(capability: str, user_query: str, client: RedditClient) -> str:
    config = LLMConfig.from_env()
    tools = _make_tools(client)
    agent = create_agent(config, tools, PROMPTS[capability])
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    return str(result["messages"][-1].content)

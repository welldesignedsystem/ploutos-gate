from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..client import RedditClient


def register_tools(mcp: FastMCP, get_client: Callable[[], RedditClient]) -> None:
    @mcp.tool(
        name="reddit_search_posts",
        description="Search Reddit posts by keyword across all subreddits or within a specific subreddit.",
    )
    def search_posts(
        query: str,
        subreddit: str | None = None,
        sort: str = "relevance",
        limit: int = 10,
        time_filter: str = "all",
    ) -> str:
        results = get_client().search_posts(
            query=query,
            subreddit=subreddit,
            sort=sort,
            limit=min(limit, 100),
            time_filter=time_filter,
        )
        return _format_posts(results)


def _format_posts(posts: list[dict]) -> str:
    if not posts:
        return "No results found."
    lines = []
    for p in posts:
        lines.append(
            f"**{p['title']}**\n"
            f"  r/{p['subreddit']} | u/{p['author']} | ↑{p['score']} | {p['num_comments']} comments\n"
            f"  {p['permalink']}\n"
        )
    return "\n".join(lines)

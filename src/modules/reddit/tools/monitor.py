from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..client import RedditClient


def register_tools(mcp: FastMCP, get_client: Callable[[], RedditClient]) -> None:
    @mcp.tool(
        name="reddit_track_mentions",
        description="Search for multiple comma-separated keywords across subreddits. Returns matches grouped by keyword.",
    )
    def track_mentions(
        keywords: str,
        subreddits: str = "",
        limit: int = 100,
        time_filter: str = "week",
    ) -> str:
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        sub_list = [s.strip() for s in subreddits.split(",") if s.strip()] if subreddits else None
        results = get_client().track_mentions(
            keywords=kw_list,
            subreddits=sub_list,
            limit=min(limit, 100),
            time_filter=time_filter,
        )
        if not results:
            return "No mentions found."
        lines = []
        for r in results:
            lines.append(
                f"[{r['keyword']}] **{r['title']}**\n"
                f"  r/{r['subreddit']} | ↑{r['score']} | {r['permalink']}\n"
            )
        return "\n".join(lines)

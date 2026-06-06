from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..client import RedditClient


def register_tools(mcp: FastMCP, get_client: Callable[[], RedditClient]) -> None:
    @mcp.tool(
        name="reddit_subreddit_info",
        description="Get metadata about a subreddit: subscribers, description, rules, etc.",
    )
    def subreddit_info(subreddit: str) -> str:
        info = get_client().subreddit_info(subreddit)
        return (
            f"**r/{info['display_name']}** — {info['title']}\n"
            f"Subscribers: {info['subscribers']:,} | Active: {info.get('active_user_count', '?')}\n"
            f"NSFW: {info['over18']}\n"
            f"---\n"
            f"{info['description'] or 'No description.'}"
        )

    @mcp.tool(
        name="reddit_user_info",
        description="Get metadata about a Reddit user: karma, account age, etc.",
    )
    def user_info(username: str) -> str:
        info = get_client().user_info(username)
        return (
            f"**u/{info['name']}**\n"
            f"Link karma: {info['link_karma']:,} | Comment karma: {info['comment_karma']:,}\n"
            f"Employee: {info['is_employee']} | Mod: {info['is_mod']}"
        )

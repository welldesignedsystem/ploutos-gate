from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..client import RedditClient


def register_tools(mcp: FastMCP, get_client: Callable[[], RedditClient]) -> None:
    @mcp.tool(
        name="reddit_create_post",
        description="Submit a text or link post to a subreddit.",
    )
    def create_post(
        subreddit: str,
        title: str,
        text: str = "",
        url: str = "",
    ) -> str:
        text_val = text or None
        url_val = url or None
        post = get_client().create_post(
            subreddit=subreddit,
            title=title,
            text=text_val,
            url=url_val,
        )
        return (
            f"Post created in r/{post['subreddit']}\n"
            f"**{post['title']}**\n"
            f"↑{post['score']} | {post['permalink']}"
        )

    @mcp.tool(
        name="reddit_reply",
        description="Reply to a Reddit post or comment by ID.",
    )
    def reply(parent_id: str, body: str) -> str:
        result = get_client().reply(parent_id=parent_id, body=body)
        return f"Reply posted: {result['id']}"

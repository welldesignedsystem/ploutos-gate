from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..client import RedditClient


def register_tools(mcp: FastMCP, get_client: Callable[[], RedditClient]) -> None:
    @mcp.tool(
        name="reddit_get_post",
        description="Fetch a Reddit post by ID including its top-level comments.",
    )
    def get_post(post_id: str) -> str:
        post = get_client().get_post(post_id)
        lines = [
            f"**{post['title']}**",
            f"r/{post['subreddit']} | u/{post['author']} | ↑{post['score']} ({post['upvote_ratio']:.0%})",
            f"---",
            f"{post['selftext']}" if post['selftext'] else "",
            f"---",
            f"**Comments ({len(post['comments'])})**",
        ]
        for c in post["comments"]:
            lines.append(f"  u/{c['author']} ↑{c['score']}: {c['body'][:200]}")
        return "\n".join(lines)

    @mcp.tool(
        name="reddit_read_subreddit",
        description="Browse a subreddit by hot, new, top, or rising posts.",
    )
    def read_subreddit(
        subreddit: str,
        sort: str = "hot",
        limit: int = 25,
        time_filter: str | None = None,
    ) -> str:
        posts = get_client().read_subreddit(
            subreddit=subreddit,
            sort=sort,
            limit=min(limit, 100),
            time_filter=time_filter,
        )
        if not posts:
            return f"No posts found in r/{subreddit}."
        lines = [f"r/{subreddit} - {sort} posts:"]
        for p in posts:
            lines.append(
                f"  [{p['score']}] {p['title']} ({p['num_comments']} comments)\n"
                f"    {p['permalink']}"
            )
        return "\n".join(lines)

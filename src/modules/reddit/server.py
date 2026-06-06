import os
from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP

from .client import RedditClient
from .config import RedditConfig
from .tools import browse, info, monitor, search, write

mcp = FastMCP("Reddit", instructions="Reddit search, browse, and engagement tools for SEO/AEO/GEO research.")

_client: RedditClient | None = None


def _get_client() -> RedditClient:
    global _client
    if _client is None:
        config = RedditConfig.from_env()
        if not config.client_id or not config.client_secret:
            raise RuntimeError(
                "Reddit API credentials not configured. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
            )
        _client = RedditClient(config)
    return _client


search.register_tools(mcp, _get_client)
browse.register_tools(mcp, _get_client)
info.register_tools(mcp, _get_client)
monitor.register_tools(mcp, _get_client)
write.register_tools(mcp, _get_client)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

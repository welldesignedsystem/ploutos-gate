from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP  # noqa: E402

from .analyze.tools import register as analyze_register  # noqa: E402
from .client import RedditClient  # noqa: E402
from .config import RedditConfig  # noqa: E402

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


analyze_register.register_tools(mcp, _get_client)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

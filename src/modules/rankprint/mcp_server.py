from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP  # noqa: E402

from .client import scan  # noqa: E402
from .models import CompanyScanOutput, ScanRequest  # noqa: E402

mcp = FastMCP(
    "Rankprint",
    instructions="Scan a company URL against search engines to measure visibility for relevant queries.",
)


@mcp.tool(
    name="rankprint_scan",
    description=(
        "Scan a company URL against DuckDuckGo search results. "
        "Given a URL and seed terms, extracts a business profile via LLM, "
        "generates relevant search queries, runs them, and returns ranked visibility results."
    ),
)
async def rankprint_scan(params: ScanRequest) -> CompanyScanOutput:
    return await scan(
        str(params.url),
        params.terms,
        max_queries=params.max_queries,
        results_per_query=params.results_per_query,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

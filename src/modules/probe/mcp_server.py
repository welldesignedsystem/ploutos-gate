from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP  # noqa: E402

from .client import probe  # noqa: E402
from .models import ProbeOutput, ProbeRequest  # noqa: E402

mcp = FastMCP(
    "Probe",
    instructions="Analyze a company URL to generate competitor-finding search terms with LLM reasoning.",
)


@mcp.tool(
    name="probe_scan",
    description=(
        "Analyze a company URL, extract its business profile, and generate "
        "competitor-finding search terms. Each term includes LLM reasoning "
        "for why it would surface relevant competitors."
    ),
)
async def probe_scan(params: ProbeRequest) -> ProbeOutput:
    return await probe(
        str(params.url),
        max_terms=params.max_terms,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from .client import scan  # noqa: E402
from .models import ScanRequest  # noqa: E402

app = FastAPI(title="Rankprint API", version="0.1.0")


@app.post("/api/scan")
async def api_scan(body: ScanRequest) -> JSONResponse:
    result = await scan(
        str(body.url),
        body.terms,
        max_queries=body.max_queries,
        results_per_query=body.results_per_query,
    )
    return JSONResponse(content=result.model_dump(mode="json"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

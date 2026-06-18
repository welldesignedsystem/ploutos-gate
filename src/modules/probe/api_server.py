from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from .client import probe  # noqa: E402
from .models import ProbeRequest  # noqa: E402

app = FastAPI(title="Probe API", version="0.1.0")


@app.post("/api/probe")
async def api_probe(body: ProbeRequest) -> JSONResponse:
    result = await probe(
        str(body.url),
        max_terms=body.max_terms,
    )
    return JSONResponse(content=result.model_dump(mode="json"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

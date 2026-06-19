import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from website_analyzer.analyzer import analyze_company
from website_analyzer.competitors import search_competitors
from website_analyzer.crawler import crawl_website
from website_analyzer.models import CompetitorGroup, CompetitorSelection
from website_analyzer.search import generate_search_queries, format_search_context
from website_analyzer.search_sources import list_sources

load_dotenv()


class AnalyzeRequest(BaseModel):
    url: str
    max_terms: int = 5


class AnalyzeResponse(BaseModel):
    company_name: str
    domain_url: str
    business_domain: str
    products: list[str]
    audience: list[str]
    categories: list[str]
    terms: list[str]


class ErrorResponse(BaseModel):
    detail: str


class CompetitorsRequest(BaseModel):
    selections: list[CompetitorSelection]
    sources: list[str] | None = None
    max_results: int = 5


class CompetitorsResponse(BaseModel):
    results: list[CompetitorGroup]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Ploutos Gateway — Website Analyzer",
    description="Analyze a company website using AI to extract structured business information.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def analyze(req: AnalyzeRequest):
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        crawl_content = await crawl_website(url)
        if not crawl_content:
            raise HTTPException(status_code=400, detail="No content could be extracted from the website.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to crawl website: {e}")

    try:
        search_queries = await generate_search_queries(crawl_content, max_terms=req.max_terms)
    except Exception:
        search_queries = []

    try:
        search_context = format_search_context(search_queries) if search_queries else ""
    except Exception:
        search_context = ""

    try:
        profile = await analyze_company(url, crawl_content, search_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    return AnalyzeResponse(**profile.model_dump())


@app.post("/competitors", response_model=CompetitorsResponse, responses={400: {"model": ErrorResponse}})
async def competitors(req: CompetitorsRequest):
    if not req.selections:
        raise HTTPException(status_code=400, detail="At least one selection is required.")

    sources = req.sources or list_sources()
    for s in sources:
        if s not in list_sources():
            raise HTTPException(status_code=400, detail=f"Unknown source: {s}. Available: {list_sources()}")

    try:
        groups = await search_competitors(req.selections, sources=sources, max_results=req.max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitor search failed: {e}")

    return CompetitorsResponse(results=groups)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host=host, port=port, reload=True)

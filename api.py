import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from website_analyzer.analyzer import analyze_company
from website_analyzer.auth import (
    register_user,
    verify_user,
    request_otp,
    verify_otp,
    refresh_access_token,
)
from website_analyzer.competitors import search_competitors
from website_analyzer.crawler import crawl_website
from website_analyzer.deps import require_auth
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


# ── Auth request/response models ──

class RegisterRequest(BaseModel):
    name: str
    email: str


class VerifyRequest(BaseModel):
    email: str
    code: str


class OtpRequest(BaseModel):
    email: str


class OtpVerifyRequest(BaseModel):
    email: str
    code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
    expires_in: int
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    sub: str
    email: str
    name: str


# ── App ──

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


# ── Auth endpoints ──

@app.post("/auth/register", responses={400: {"model": ErrorResponse}})
async def register(req: RegisterRequest):
    try:
        return register_user(req.name, req.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/verify", responses={400: {"model": ErrorResponse}})
async def verify(req: VerifyRequest):
    try:
        return verify_user(req.email, req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login", response_model=dict, responses={400: {"model": ErrorResponse}})
async def login(req: OtpRequest):
    try:
        return request_otp(req.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login/verify", response_model=TokenResponse, responses={400: {"model": ErrorResponse}})
async def login_verify(req: OtpVerifyRequest):
    try:
        return verify_otp(req.email, req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/refresh", response_model=TokenResponse, responses={400: {"model": ErrorResponse}})
async def refresh(req: RefreshRequest):
    try:
        return refresh_access_token(req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/me", response_model=UserResponse, responses={401: {"model": ErrorResponse}})
async def me(user: dict = Depends(require_auth)):
    return UserResponse(sub=user.get("sub", ""), email=user.get("email", ""), name=user.get("name", ""))


# ── Protected endpoints ──

@app.post("/analyze", response_model=AnalyzeResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def analyze(req: AnalyzeRequest, user: dict = Depends(require_auth)):
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


@app.post("/competitors", response_model=CompetitorsResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
async def competitors(req: CompetitorsRequest, user: dict = Depends(require_auth)):
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

import json
import os
import time
from contextlib import asynccontextmanager

import boto3
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
from website_analyzer.contact import send_contact_email
from website_analyzer.crawler import crawl_website
from website_analyzer.deps import require_auth
from website_analyzer.models import CompetitorGroup, CompetitorSelection
from website_analyzer.search import generate_search_queries, format_search_context
from website_analyzer.search_sources import list_sources
from common.store import create_store

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
    url: str = ""
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


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str
    plan: str | None = None


class ContactResponse(BaseModel):
    message: str


# ── Data stores ──

analyze_store = create_store("ploutos-analyze")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/deep")
async def health_deep():
    checks = {}

    # Env vars
    required_vars = ["TAVILY_API_KEY", "COGNITO_USER_POOL_ID", "COGNITO_CLIENT_ID"]
    env_checks = {}
    for var in required_vars:
        env_checks[var] = bool(os.getenv(var))
    checks["env"] = env_checks

    # Bedrock client init
    try:
        region = os.getenv("AWS_REGION", "us-east-1")
        role_arn = os.getenv("BEDROCK_ASSUME_ROLE_ARN")
        if role_arn:
            sts = boto3.client("sts", region_name=region)
            sts.assume_role(RoleArn=role_arn, RoleSessionName="health-check", DurationSeconds=900)
        client = boto3.client("bedrock-runtime", region_name=region)
        checks["bedrock"] = {"ok": True, "region": region, "role_arn": bool(role_arn)}
    except Exception as e:
        checks["bedrock"] = {"ok": False, "error": str(e)}

    # SES client init
    try:
        ses = boto3.client("sesv2", region_name=os.getenv("CONTACT_REGION", "us-east-1"))
        checks["ses"] = {"ok": True}
    except Exception as e:
        checks["ses"] = {"ok": False, "error": str(e)}

    # Cognito client init
    try:
        cognito = boto3.client("cognito-idp", region_name=os.getenv("COGNITO_REGION", "us-east-1"))
        checks["cognito"] = {"ok": True, "user_pool_id": bool(os.getenv("COGNITO_USER_POOL_ID"))}
    except Exception as e:
        checks["cognito"] = {"ok": False, "error": str(e)}

    all_ok = all(c.get("ok", False) for c in checks.values())
    status_code = 200 if all_ok else 503

    return {"status": "ok" if all_ok else "degraded", "checks": checks, "timestamp": time.time()}


# ── Contact endpoint ──

@app.post("/contact", response_model=ContactResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def contact(req: ContactRequest):
    if not req.name.strip() or not req.email.strip() or not req.message.strip():
        raise HTTPException(status_code=400, detail="Name, email, and message are required.")
    try:
        return send_contact_email(req.name.strip(), req.email.strip(), req.message.strip(), req.plan)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login/verify", response_model=TokenResponse, responses={400: {"model": ErrorResponse}})
async def login_verify(req: OtpVerifyRequest):
    try:
        return verify_otp(req.email, req.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/refresh", response_model=TokenResponse, responses={400: {"model": ErrorResponse}})
async def refresh(req: RefreshRequest):
    try:
        return refresh_access_token(req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/me", response_model=UserResponse, responses={401: {"model": ErrorResponse}})
async def me(user: dict = Depends(require_auth)):
    return UserResponse(sub=user.get("sub", ""), email=user.get("email", ""), name=user.get("name", ""))


# ── Cached data endpoints ──

@app.get("/analyze/{url:path}", responses={404: {"model": ErrorResponse}})
async def get_cached_analyze(url: str, user: dict = Depends(require_auth)):
    item = analyze_store.get(user.get("sub"), url)
    if not item:
        raise HTTPException(status_code=404, detail="No cached analysis found.")
    return {"profile": item["data"], "updatedAt": item["updatedAt"]}


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

    analyze_store.put(user.get("sub"), url, profile.model_dump())
    return AnalyzeResponse(**profile.model_dump())


async def _stream_analyze(url: str, max_terms: int, user_id: str):
    def _event(event_type: str, data: object) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    yield _event("log", {"message": f"Starting analysis of {url}…"})

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    yield _event("log", {"message": "Scanning homepage…"})
    try:
        crawl_content = await crawl_website(url)
        if not crawl_content:
            yield _event("error", {"message": "No content could be extracted from the website."})
            return
        char_count = len(crawl_content)
        yield _event("log", {"message": f"Homepage scanned ({char_count:,} characters)"})
    except Exception as e:
        yield _event("error", {"message": f"Failed to scan website: {e}"})
        return

    yield _event("log", {"message": "Generating research queries…"})
    try:
        search_queries = await generate_search_queries(crawl_content, max_terms=max_terms)
        yield _event("log", {"message": f"Generated {len(search_queries)} search queries"})
    except Exception:
        search_queries = []
        yield _event("log", {"message": "No search queries generated"})

    yield _event("log", {"message": "Searching for company information…"})
    try:
        search_context = format_search_context(search_queries) if search_queries else ""
        yield _event("log", {"message": "Search results gathered"})
    except Exception:
        search_context = ""
        yield _event("log", {"message": "No search results available"})

    yield _event("log", {"message": "Building company profile…"})
    try:
        profile = await analyze_company(url, crawl_content, search_context)
        analyze_store.put(user_id, url, profile.model_dump())
        yield _event("log", {"message": "Company profile saved"})
        yield _event("result", {"profile": profile.model_dump()})
    except Exception as e:
        yield _event("error", {"message": f"Analysis failed: {e}"})


@app.post("/analyze/stream", responses={401: {"model": ErrorResponse}})
async def analyze_stream(req: AnalyzeRequest, user: dict = Depends(require_auth)):
    url = req.url.strip()
    return StreamingResponse(
        _stream_analyze(url, max_terms=req.max_terms, user_id=user.get("sub")),
        media_type="text/event-stream",
    )


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

# Ploutos Gateway — Agent Context

## Project

**Ploutos Gateway** — FastAPI backend for website analysis (crawl + LLM extraction) and competitor search (multi-source aggregation + LLM filtering) with Cognito-native passwordless OTP authentication.

Python 3.12, uv-managed virtual env (`.venv/`).

## Auth Flow (Cognito passwordless OTP)

Uses Cognito's `ForgotPassword` + `USER_PASSWORD_AUTH` flow:

1. **`POST /auth/register`** — `sign_up` with auto-generated password → verification code to email
2. **`POST /auth/verify`** — `confirm_sign_up(code)` → user confirmed
3. **`POST /auth/login`** — `forgot_password(email)` → OTP code to email
4. **`POST /auth/login/verify`** — `confirm_forgot_password(code, new_password)` + `initiate_auth(USER_PASSWORD_AUTH, new_password)` → tokens
5. **`GET /auth/me`** — JWKS-verified ID token → user profile (sub, email, name)
6. **`POST /auth/refresh`** — `REFRESH_TOKEN_AUTH` → new access_token

**Token verification**: `python-jose[cryptography]` fetches Cognito JWKS from `https://cognito-idp.{region}.amazonaws.com/{poolId}/.well-known/jwks.json`, verifies RSA signature, audience (client_id), and issuer.

**Pool config**: `default-aws-cognito-pool` with client `default-aws-cognito-client`. `USER_AUTH` flow was tried but `EMAIL_OTP` challenge requires `SignInPolicy` API not yet available in boto3. `ForgotPassword` is the working fallback.

**Important**: `/auth/me` requires the **id_token** (not access_token). Use `HTTPBearer` with `Authorization: Bearer <id_token>`.

## Architecture

```
api.py                          # FastAPI app, routes, request/response models
website_analyzer/
├── __init__.py
├── auth.py                     # Cognito auth: register, verify, forgot-password OTP, JWKS verify, refresh
├── deps.py                     # FastAPI Depends(require_auth) via HTTPBearer
├── models.py                   # Pydantic models: CompanyProfile, CompetitorSelection, etc.
├── llm.py                      # ChatBedrock (Claude Haiku) with env config
├── crawler.py                  # Crawl4AI AsyncHTTPCrawlerStrategy (no Playwright)
├── search.py                   # LLM query generation + Tavily search
├── analyzer.py                 # LangChain structured output → CompanyProfile
├── competitors.py              # Multi-source competitor search + LLM filter
└── search_sources/
    ├── __init__.py             # Plugin registry + factory
    ├── base.py                 # SearchSource ABC
    ├── tavily_source.py        # Tavily implementation
    └── duckduckgo_source.py    # DuckDuckGo via ddgs library
setup-cognito.py                # One-time script to create Cognito pool + client
start.sh                        # uv run uvicorn api:app --reload
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/auth/register` | No | Sign up (verification code to email) |
| POST | `/auth/verify` | No | Confirm sign-up with code |
| POST | `/auth/login` | No | Request OTP via forgot-password |
| POST | `/auth/login/verify` | No | Verify OTP → tokens |
| POST | `/auth/refresh` | No | Refresh access token |
| GET | `/auth/me` | Yes | User profile from ID token |
| POST | `/analyze` | Yes | Crawl website + LLM extraction → CompanyProfile |
| POST | `/competitors` | Yes | Search competitors via Tavily/DDG + LLM filter |

## Key Decisions & Constraints

- **No Playwright** — Ubuntu 26.04 unsupported. Crawl4AI uses `AsyncHTTPCrawlerStrategy`.
- **No custom JWT/PyJWT** — Cognito issues RSA tokens, verified via JWKS endpoint with `python-jose[cryptography]`.
- **Cognito sends all emails** — SES integration for OTP delivery is stubbed via Cognito's default email sender.
- **LLM**: AWS Bedrock (Claude Haiku) via `langchain-aws`. Requires `aws login` for active session.
- **Search**: Tavily (API key in `.env`) + DuckDuckGo (via `ddgs` library, no key needed).
- **`CompetitorSelection`** — all four fields optional; `model_validator` rejects if all empty.
- **`CompetitorResult.url`** — stores closest full URL from search result.
- **Competitor filter** — `BLOCKED_DOMAINS` set strips social/video/Wikipedia/forums before LLM filter. LLM prompt removes blogs, guides, listicles. Falls back to unfiltered if Bedrock unavailable.
- **Search sources plugin pattern** — `SearchSource` ABC + registry factory; add source = one file + `register_source()` call.
- **Data output** — returned as JSON, never stored.

## Running

```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
# or
./start.sh
```

## .env Required Keys

```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
TAVILY_API_KEY=
TAVILY_SEARCH_URL=https://api.tavily.com
BEDROCK_MODEL=us.anthropic.claude-haiku-4-5-20251001-v1:0
COGNITO_USER_POOL_ID=us-east-1_XXXX
COGNITO_CLIENT_ID=XXXXXXXXXX
COGNITO_REGION=us-east-1
```

## Setup (one-time)

```bash
uv run python setup-cognito.py   # Creates pool, prints IDs
# Copy IDs to .env
```

## Current Pool

- **Pool ID**: set in `.env` as `COGNITO_USER_POOL_ID`
- **Client ID**: set in `.env` as `COGNITO_CLIENT_ID`
- **Region**: `us-east-1`
- **Pool name**: `default-aws-cognito-pool`
- **Client name**: `default-aws-cognito-client`

## Session History

- Pool was recreated after accidental deletion on 2026-06-20 (twice — current ID `us-east-1_0GFUsYiZ3`).
- Auth rewritten from `USER_AUTH` + `EMAIL_OTP` challenge (blocked by unavailable `SignInPolicy` API) to `ForgotPassword` + `USER_PASSWORD_AUTH` flow.
- `HTTPBearer` added to `deps.py` for Swagger UI "Authorize" button support.
- `setup-cognito.sh` deleted (stale shell script, superseded by `.py`).
- Old pools `us-east-1_DRax2BSZ7` and `us-east-1_wmpa65J2L` deleted.

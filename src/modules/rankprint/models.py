from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

SearchSurface = Literal["seo", "aeo", "geo"]


class ScanRequest(BaseModel):
    url: HttpUrl
    terms: list[str] = Field(
        default_factory=list,
        max_length=25,
        description="Seed terms; auto-derived from website if empty",
    )
    max_queries: int = Field(default=10, ge=1, le=25, description="Number of search queries to generate")
    results_per_query: int = Field(default=10, ge=1, le=50, description="Results to return per query per provider")


class BusinessProfile(BaseModel):
    url: str
    domain: str
    name: str | None = None
    description: str | None = None
    products: list[str] = Field(default_factory=list)
    audiences: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class GeneratedSearchQuery(BaseModel):
    query: str
    intent: Literal["informational", "commercial", "transactional", "navigational"]
    surface: SearchSurface
    reason: str


class TextReference(BaseModel):
    source: Literal["title", "snippet", "page", "answer", "citation"]
    text: str
    relevance: str


class RankedReference(BaseModel):
    rank: int | None = None
    title: str | None = None
    url: str | None = None
    domain: str | None = None
    text_reference: TextReference


class ProviderResult(BaseModel):
    provider: str
    surface: SearchSurface
    found: bool
    best_rank: int | None = None
    matches: list[RankedReference] = Field(default_factory=list)
    competitors: list[RankedReference] = Field(default_factory=list)
    raw_answer: str | None = None
    citations: list[str] = Field(default_factory=list)
    text_reference: TextReference | None = None


class QueryResult(GeneratedSearchQuery):
    provider_results: list[ProviderResult] = Field(default_factory=list)


class SkippedProvider(BaseModel):
    provider: str
    reason: str


class ScanSummary(BaseModel):
    queries_generated: int
    providers_run: int
    providers_skipped: int
    total_checks: int
    checks_found: int
    best_rank: int | None = None
    average_best_rank: float | None = None
    visibility_score: int


class CompanyScanOutput(BaseModel):
    company: BusinessProfile
    query_results: list[QueryResult]
    skipped_providers: list[SkippedProvider]
    summary: ScanSummary

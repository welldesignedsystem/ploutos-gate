import pydantic
import pytest

from rankprint.models import (
    BusinessProfile,
    CompanyScanOutput,
    GeneratedSearchQuery,
    ProviderResult,
    QueryResult,
    RankedReference,
    ScanRequest,
    ScanSummary,
    TextReference,
)


def test_scan_request_valid():
    r = ScanRequest(url="https://example.com", terms=["ai", "software"])
    assert str(r.url) == "https://example.com/"
    assert r.terms == ["ai", "software"]


def test_scan_request_no_terms():
    r = ScanRequest(url="https://example.com")
    assert r.terms == []
    assert r.max_queries == 10


def test_scan_request_too_many_terms():
    with pytest.raises(pydantic.ValidationError):
        ScanRequest(url="https://example.com", terms=["t"] * 26)


def test_scan_request_invalid_url():
    with pytest.raises(pydantic.ValidationError):
        ScanRequest(url="not-a-url", terms=["test"])


def test_scan_request_defaults():
    r = ScanRequest(url="https://example.com", terms=["test"])
    assert r.max_queries == 10
    assert r.results_per_query == 10


def test_scan_request_max_queries_clamped():
    with pytest.raises(pydantic.ValidationError):
        ScanRequest(url="https://example.com", terms=["test"], max_queries=0)
    with pytest.raises(pydantic.ValidationError):
        ScanRequest(url="https://example.com", terms=["test"], max_queries=26)
    r = ScanRequest(url="https://example.com", terms=["test"], max_queries=5)
    assert r.max_queries == 5


def test_scan_request_results_per_query_clamped():
    with pytest.raises(pydantic.ValidationError):
        ScanRequest(url="https://example.com", terms=["test"], results_per_query=0)
    with pytest.raises(pydantic.ValidationError):
        ScanRequest(url="https://example.com", terms=["test"], results_per_query=51)
    r = ScanRequest(url="https://example.com", terms=["test"], results_per_query=20)
    assert r.results_per_query == 20


def test_business_profile_defaults():
    p = BusinessProfile(url="https://example.com", domain="example.com")
    assert p.name is None
    assert p.products == []
    assert p.audiences == []
    assert p.categories == []


def test_generated_search_query():
    q = GeneratedSearchQuery(
        query="best ai receptionist",
        intent="commercial",
        surface="seo",
        reason="test",
    )
    assert q.query == "best ai receptionist"
    assert q.intent == "commercial"
    assert q.surface == "seo"


def test_generated_search_query_invalid_intent():
    with pytest.raises(pydantic.ValidationError):
        GeneratedSearchQuery(query="test", intent="invalid", surface="seo", reason="test")


def test_text_reference():
    t = TextReference(source="snippet", text="some text", relevance="high")
    assert t.source == "snippet"


def test_ranked_reference_with_url():
    r = RankedReference(
        rank=1,
        title="Test",
        url="https://example.com/page",
        domain="example.com",
        text_reference=TextReference(source="snippet", text="desc", relevance="high"),
    )
    assert r.rank == 1


def test_ranked_reference_without_url():
    r = RankedReference(
        rank=2,
        text_reference=TextReference(source="title", text="foo", relevance="low"),
    )
    assert r.url is None


def test_provider_result_no_matches():
    p = ProviderResult(provider="duckduckgo", surface="seo", found=False)
    assert p.best_rank is None
    assert p.matches == []


def test_provider_result_with_matches():
    ref = RankedReference(
        rank=1,
        text_reference=TextReference(source="snippet", text="x", relevance="y"),
    )
    p = ProviderResult(
        provider="duckduckgo",
        surface="seo",
        found=True,
        best_rank=1,
        matches=[ref],
    )
    assert p.found is True
    assert len(p.matches) == 1


def test_query_result():
    qr = QueryResult(
        query="test query",
        intent="informational",
        surface="seo",
        reason="testing",
        provider_results=[
            ProviderResult(provider="duckduckgo", surface="seo", found=False),
        ],
    )
    assert len(qr.provider_results) == 1


def test_scan_summary():
    s = ScanSummary(
        queries_generated=5,
        providers_run=1,
        providers_skipped=0,
        total_checks=5,
        checks_found=3,
        best_rank=1,
        average_best_rank=2.3,
        visibility_score=60,
    )
    assert s.visibility_score == 60


def test_company_scan_output():
    company = BusinessProfile(url="https://example.com", domain="example.com")
    query_results = [
        QueryResult(
            query="test",
            intent="informational",
            surface="seo",
            reason="test",
        ),
    ]
    summary = ScanSummary(
        queries_generated=1,
        providers_run=0,
        providers_skipped=1,
        total_checks=0,
        checks_found=0,
        visibility_score=0,
    )
    out = CompanyScanOutput(
        company=company,
        query_results=query_results,
        skipped_providers=[],
        summary=summary,
    )
    assert out.company.domain == "example.com"
    assert len(out.query_results) == 1

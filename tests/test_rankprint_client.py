import os
from unittest.mock import AsyncMock, patch

import pytest

from rankprint.client import _domain_matches, _extract_profile, _generate_queries, scan
from rankprint.models import (
    BusinessProfile,
    GeneratedSearchQuery,
)


class TestDomainMatches:
    def test_exact_match(self):
        assert _domain_matches("example.com", "example.com") is True

    def test_subdomain_match(self):
        assert _domain_matches("www.example.com", "example.com") is True
        assert _domain_matches("blog.example.com", "example.com") is True

    def test_www_prefix_normalized(self):
        assert _domain_matches("example.com", "www.example.com") is True

    def test_no_match(self):
        assert _domain_matches("other.com", "example.com") is False

    def test_case_insensitive(self):
        assert _domain_matches("Example.Com", "example.com") is True


class TestExtractProfile:
    @pytest.mark.asyncio
    async def test_no_page_text(self):
        config = AsyncMock()
        result = await _extract_profile("https://ex.com", "ex.com", None, config)
        assert result is None

    @pytest.mark.asyncio
    async def test_llm_returns_profile(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = BusinessProfile(
                url="https://ex.com",
                domain="ex.com",
                name="Example Corp",
                description="A company",
            )
            result = await _extract_profile(
                "https://ex.com",
                "ex.com",
                "some text",
                AsyncMock(),
            )
            assert result is not None
            assert result.name == "Example Corp"

    @pytest.mark.asyncio
    async def test_llm_returns_none(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _extract_profile(
                "https://ex.com",
                "ex.com",
                "some text",
                AsyncMock(),
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_llm_raises(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.side_effect = Exception("LLM error")
            result = await _extract_profile(
                "https://ex.com",
                "ex.com",
                "some text",
                AsyncMock(),
            )
            assert result is None


class TestGenerateQueries:
    @pytest.mark.asyncio
    async def test_llm_returns_queries(self):
        fake_queries = [
            GeneratedSearchQuery(
                query="best ai software",
                intent="commercial",
                surface="seo",
                reason="test",
            ),
        ]
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = fake_queries
            result = await _generate_queries(None, ["ai"], AsyncMock())
            assert len(result) == 1
            assert result[0].query == "best ai software"

    @pytest.mark.asyncio
    async def test_fallback_to_raw_terms(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_queries(None, ["ai", "software"], AsyncMock())
            assert len(result) == 2
            assert result[0].query == "ai"
            assert result[0].intent == "informational"
            assert result[0].surface == "seo"

    @pytest.mark.asyncio
    async def test_fallback_on_llm_exception(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.side_effect = Exception("LLM down")
            result = await _generate_queries(
                None,
                ["fallback-term"],
                AsyncMock(),
            )
            assert len(result) == 1
            assert result[0].query == "fallback-term"

    @pytest.mark.asyncio
    async def test_max_queries_truncates_llm_output(self):
        fake_queries = [
            GeneratedSearchQuery(query=f"q{i}", intent="informational", surface="seo", reason="x") for i in range(5)
        ]
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = fake_queries
            result = await _generate_queries(None, ["t"], AsyncMock(), max_queries=2)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_max_queries_truncates_fallback(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_queries(
                None,
                ["a", "b", "c", "d", "e"],
                AsyncMock(),
                max_queries=3,
            )
            assert len(result) == 3
            assert [q.query for q in result] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_fallback_empty_terms_with_profile(self):
        profile = BusinessProfile(url="https://ex.com", domain="ex.com", name="ExampleCorp")
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_queries(profile, [], AsyncMock())
            assert len(result) == 1
            assert result[0].query == "ExampleCorp"

    @pytest.mark.asyncio
    async def test_fallback_empty_terms_no_profile(self):
        with patch("rankprint.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_queries(None, [], AsyncMock())
            assert result == []


class TestScan:
    @pytest.mark.asyncio
    async def test_full_scan_flow(self):
        with (
            patch("rankprint.client.fetch_page_text") as mock_fetch,
            patch("rankprint.client._extract_profile") as mock_profile,
            patch("rankprint.client._generate_queries") as mock_queries,
            patch("rankprint.client.DuckDuckGoChecker.search") as mock_search,
        ):
            mock_fetch.return_value = "page text"
            mock_profile.return_value = BusinessProfile(
                url="https://example.com",
                domain="example.com",
                name="Test Co",
            )
            mock_queries.return_value = [
                GeneratedSearchQuery(
                    query="test query",
                    intent="informational",
                    surface="seo",
                    reason="test",
                ),
            ]
            mock_search.return_value = [
                {
                    "title": "Result 1",
                    "url": "https://example.com/page",
                    "domain": "example.com",
                    "snippet": "About Test Co",
                },
                {
                    "title": "Result 2",
                    "url": "https://competitor.com/page",
                    "domain": "competitor.com",
                    "snippet": "Competitor",
                },
            ]

            output = await scan("https://example.com", ["test term"])

            assert output.company.name == "Test Co"
            assert len(output.query_results) == 1
            qr = output.query_results[0]
            assert qr.query == "test query"
            assert len(qr.provider_results) == 1
            pr = qr.provider_results[0]
            assert pr.provider == "duckduckgo"
            assert pr.found is True
            assert pr.best_rank == 1
            assert len(pr.matches) == 1
            assert len(pr.competitors) == 1
            assert output.summary.checks_found == 1
            assert output.summary.total_checks == 1
            assert output.summary.visibility_score == 100

    @pytest.mark.asyncio
    async def test_scan_no_results_found(self):
        with (
            patch("rankprint.client.fetch_page_text") as mock_fetch,
            patch("rankprint.client._extract_profile") as mock_profile,
            patch("rankprint.client._generate_queries") as mock_queries,
            patch("rankprint.client.DuckDuckGoChecker.search") as mock_search,
        ):
            mock_fetch.return_value = None
            mock_profile.return_value = None
            mock_queries.return_value = [
                GeneratedSearchQuery(
                    query="no results",
                    intent="informational",
                    surface="seo",
                    reason="test",
                ),
            ]
            mock_search.return_value = []

            output = await scan("https://example.com", ["test"])

            assert output.company.domain == "example.com"
            assert len(output.query_results) == 1
            assert output.query_results[0].provider_results[0].found is False
            assert output.summary.checks_found == 0
            assert output.summary.visibility_score == 0

    @pytest.mark.asyncio
    async def test_scan_with_tavily(self):
        with (
            patch("rankprint.client.fetch_page_text") as mock_fetch,
            patch("rankprint.client._extract_profile") as mock_profile,
            patch("rankprint.client._generate_queries") as mock_queries,
            patch("rankprint.client.DuckDuckGoChecker.search") as mock_ddg,
            patch("rankprint.client.TavilyChecker.search") as mock_tavily,
            patch.dict(os.environ, {"TAVILY_API_KEY": "test-tavily-key"}),
        ):
            mock_fetch.return_value = "page text"
            mock_profile.return_value = None
            mock_queries.return_value = [
                GeneratedSearchQuery(
                    query="test query",
                    intent="commercial",
                    surface="seo",
                    reason="test",
                ),
            ]
            mock_ddg.return_value = []
            mock_tavily.return_value = [
                {
                    "title": "Tavily Result",
                    "url": "https://example.com/page",
                    "domain": "example.com",
                    "snippet": "Tavily found us",
                },
            ]

            output = await scan("https://example.com", ["test"])

            assert len(output.query_results) == 1
            qr = output.query_results[0]
            assert len(qr.provider_results) == 2
            ddg_pr = qr.provider_results[0]
            tavily_pr = qr.provider_results[1]
            assert ddg_pr.provider == "duckduckgo"
            assert ddg_pr.found is False
            assert tavily_pr.provider == "tavily"
            assert tavily_pr.found is True
            assert tavily_pr.best_rank == 1
            assert len(output.skipped_providers) == 0
            assert output.summary.providers_run == 2
            assert output.summary.visibility_score == 50

    @pytest.mark.asyncio
    async def test_scan_empty_terms(self):
        with (
            patch("rankprint.client.fetch_page_text") as mock_fetch,
            patch("rankprint.client._extract_profile") as mock_profile,
            patch("rankprint.client._generate_queries") as mock_queries,
            patch("rankprint.client.DuckDuckGoChecker.search") as mock_search,
        ):
            mock_fetch.return_value = "page text"
            mock_profile.return_value = BusinessProfile(
                url="https://example.com",
                domain="example.com",
                name="Test Co",
            )
            mock_queries.return_value = [
                GeneratedSearchQuery(
                    query="Test Co",
                    intent="informational",
                    surface="seo",
                    reason="auto-derived",
                ),
            ]
            mock_search.return_value = []

            output = await scan("https://example.com", [])

            assert output.company.name == "Test Co"
            assert len(output.query_results) == 1
            assert output.query_results[0].query == "Test Co"

from unittest.mock import AsyncMock, patch

import pytest

from probe.client import _extract_profile, _fallback_terms, _generate_terms, probe
from probe.crawler import SiteContent
from probe.models import BusinessProfile, GeneratedTerm


def make_site(text: str = "", headings: list[str] | None = None, pages: int = 1) -> SiteContent:
    s = SiteContent()
    s.text = text
    s.headings = headings or []
    s.pages_fetched = pages
    return s


class TestExtractProfile:
    @pytest.mark.asyncio
    async def test_no_content(self):
        config = AsyncMock()
        site = make_site()
        result = await _extract_profile("https://ex.com", "ex.com", site, config)
        assert result is None

    @pytest.mark.asyncio
    async def test_llm_returns_profile(self):
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = BusinessProfile(
                url="https://ex.com",
                domain="ex.com",
                name="Example Corp",
            )
            site = make_site(text="some text", headings=["About Us"])
            result = await _extract_profile(
                "https://ex.com",
                "ex.com",
                site,
                AsyncMock(),
            )
            assert result is not None
            assert result.name == "Example Corp"

    @pytest.mark.asyncio
    async def test_llm_returns_none(self):
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            site = make_site(text="text")
            result = await _extract_profile(
                "https://ex.com",
                "ex.com",
                site,
                AsyncMock(),
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_llm_raises(self):
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.side_effect = Exception("LLM error")
            site = make_site(text="text")
            result = await _extract_profile(
                "https://ex.com",
                "ex.com",
                site,
                AsyncMock(),
            )
            assert result is None


class TestGenerateTerms:
    @pytest.mark.asyncio
    async def test_llm_returns_terms(self):
        fake_terms = [
            GeneratedTerm(terms="international moving", reason="finds competitors"),
        ]
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = fake_terms
            site = make_site(text="text")
            result = await _generate_terms(None, site, AsyncMock())
            assert len(result) == 1
            assert result[0].terms == "international moving"

    @pytest.mark.asyncio
    async def test_fallback_uses_headings(self):
        site = make_site(
            text="We are a moving company.",
            headings=["International Moving", "Domestic Relocation", "Office Moving", "Storage Services"],
        )
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_terms(None, site, AsyncMock())
            assert len(result) == 4
            assert result[0].terms == "International Moving"
            assert result[1].terms == "Domestic Relocation"
            assert result[2].terms == "Office Moving"
            assert result[3].terms == "Storage Services"

    @pytest.mark.asyncio
    async def test_fallback_with_profile_name_and_headings(self):
        profile = BusinessProfile(url="https://ex.com", domain="ex.com", name="APAC Relocation")
        site = make_site(
            text="Moving services.",
            headings=["International Movers", "Local Moving"],
        )
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_terms(profile, site, AsyncMock())
            assert len(result) >= 2
            assert result[0].terms == "APAC Relocation"

    @pytest.mark.asyncio
    async def test_fallback_dedupes(self):
        site = make_site(
            text="text",
            headings=["International Moving", "International Moving", "Storage Services", "Storage Services"],
        )
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_terms(None, site, AsyncMock())
            assert len(result) == 2
            assert result[0].terms == "International Moving"
            assert result[1].terms == "Storage Services"

    @pytest.mark.asyncio
    async def test_fallback_max_terms(self):
        headings = [f"Heading {i}" for i in range(30)]
        site = make_site(text="text", headings=headings)
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_terms(None, site, AsyncMock(), max_terms=5)
            assert len(result) == 5

    @pytest.mark.asyncio
    async def test_fallback_empty(self):
        site = make_site()
        with patch("probe.client.structured_chat") as mock_chat:
            mock_chat.return_value = None
            result = await _generate_terms(None, site, AsyncMock())
            assert result == []


class TestFallbackTerms:
    def test_headings_only(self):
        site = make_site(headings=["Service A", "Service B"])
        result = _fallback_terms(site, None)
        assert len(result) == 2
        assert result[0].terms == "Service A"
        assert result[1].terms == "Service B"

    def test_profile_name_first(self):
        profile = BusinessProfile(url="https://ex.com", domain="ex.com", name="TestCo")
        site = make_site(headings=["Service A"])
        result = _fallback_terms(site, profile)
        assert result[0].terms == "TestCo"
        assert result[1].terms == "Service A"

    def test_categories_before_headings(self):
        profile = BusinessProfile(
            url="https://ex.com",
            domain="ex.com",
            name="TestCo",
            categories=["Logistics"],
        )
        site = make_site(headings=["Some Heading"])
        result = _fallback_terms(site, profile)
        assert result[0].terms == "TestCo"
        assert result[1].terms == "Logistics"
        assert result[2].terms == "Some Heading"

    def test_domain_fallback(self):
        profile = BusinessProfile(url="https://ex.com", domain="example.com")
        site = make_site()
        result = _fallback_terms(site, profile)
        assert len(result) == 1
        assert result[0].terms == "example.com"


class TestProbe:
    @pytest.mark.asyncio
    async def test_full_probe_flow(self):
        with (
            patch("probe.client.fetch_site") as mock_fetch,
            patch("probe.client._extract_profile") as mock_profile,
            patch("probe.client._generate_terms") as mock_terms,
        ):
            mock_fetch.return_value = make_site(text="page text", headings=["Service"])
            mock_profile.return_value = BusinessProfile(
                url="https://example.com",
                domain="example.com",
                name="Test Co",
            )
            mock_terms.return_value = [
                GeneratedTerm(
                    terms="competitor term",
                    reason="finds competitors",
                ),
            ]

            output = await probe("https://example.com", max_terms=10)

            assert output.url == "https://example.com"
            assert output.max_terms == 10
            assert output.target.name == "Test Co"
            assert len(output.terms) == 1
            assert output.terms[0].terms == "competitor term"

    @pytest.mark.asyncio
    async def test_probe_no_content(self):
        with (
            patch("probe.client.fetch_site") as mock_fetch,
            patch("probe.client._extract_profile") as mock_profile,
            patch("probe.client._generate_terms") as mock_terms,
        ):
            mock_fetch.return_value = make_site()
            mock_profile.return_value = None
            mock_terms.return_value = []

            output = await probe("https://example.com")

            assert output.target.domain == "example.com"
            assert output.terms == []

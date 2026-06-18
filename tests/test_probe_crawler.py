from unittest.mock import MagicMock, patch

import pytest

from probe.crawler import SiteContent, extract_domain, fetch_site


def _mock_resp(html: str) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status.return_value = None
    return resp


class TestExtractDomain:
    def test_simple(self):
        assert extract_domain("https://example.com/page") == "example.com"

    def test_www(self):
        assert extract_domain("https://www.example.com") == "www.example.com"

    def test_no_scheme(self):
        assert extract_domain("example.com") == "example.com"


class TestFetchSite:
    @pytest.mark.asyncio
    async def test_fetches_homepage(self):
        html = "<html><body><h1>Welcome</h1><p>We are a moving company.</p></body></html>"
        with patch("probe.crawler.httpx.AsyncClient") as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.return_value = _mock_resp(html)

            result = await fetch_site("https://example.com", max_pages=5)
            assert result.pages_fetched >= 1
            assert "Welcome" in result.text
            assert "moving" in result.text

    @pytest.mark.asyncio
    async def test_collects_headings(self):
        html = """
        <html><body>
        <h1>APAC Relocation</h1>
        <h2>International Moving</h2>
        <h2>Domestic Relocation</h2>
        <h3>Office Moving</h3>
        </body></html>
        """
        with patch("probe.crawler.httpx.AsyncClient") as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.return_value = _mock_resp(html)

            result = await fetch_site("https://example.com", max_pages=5)
            assert "APAC Relocation" in result.headings
            assert "International Moving" in result.headings
            assert "Domestic Relocation" in result.headings
            assert "Office Moving" in result.headings

    @pytest.mark.asyncio
    async def test_strips_noise_tags(self):
        html = """
        <html><body>
        <nav>Nav stuff</nav>
        <header>Header stuff</header>
        <footer>Footer stuff</footer>
        <aside>Side stuff</aside>
        <h1>Real Content</h1>
        </body></html>
        """
        with patch("probe.crawler.httpx.AsyncClient") as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.return_value = _mock_resp(html)

            result = await fetch_site("https://example.com", max_pages=5)
            assert "Nav stuff" not in result.text
            assert "Header stuff" not in result.text
            assert "Footer stuff" not in result.text
            assert "Real Content" in result.text

    @pytest.mark.asyncio
    async def test_follows_same_domain_links(self):
        homepage = """
        <html><body>
        <a href="/services">Services</a>
        <a href="/about">About</a>
        <a href="https://other.com">External</a>
        <h1>Home</h1>
        </body></html>
        """
        services_page = """
        <html><body>
        <h1>Our Services</h1>
        <h2>International Moving</h2>
        </body></html>
        """
        about_page = """
        <html><body>
        <h1>About Us</h1>
        </body></html>
        """
        responses = {
            "https://example.com": homepage,
            "https://example.com/services": services_page,
            "https://example.com/about": about_page,
        }

        with patch("probe.crawler.httpx.AsyncClient") as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get

            async def side_effect(url, **kwargs):
                return _mock_resp(responses.get(url, ""))

            mock_get.side_effect = side_effect

            result = await fetch_site("https://example.com", max_pages=5)
            assert result.pages_fetched >= 2
            assert "International Moving" in result.headings

    @pytest.mark.asyncio
    async def test_network_error_returns_empty(self):
        with patch("probe.crawler.httpx.AsyncClient") as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.side_effect = Exception("Network error")

            result = await fetch_site("https://example.com", max_pages=5)
            assert result.pages_fetched == 0
            assert result.text == ""
            assert result.headings == []

    @pytest.mark.asyncio
    async def test_respects_max_pages(self):
        html = "<html><body><h1>Home</h1></body></html>"
        with patch("probe.crawler.httpx.AsyncClient") as mock_client:
            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.return_value = _mock_resp(html)

            result = await fetch_site("https://example.com", max_pages=3)
            assert result.pages_fetched <= 3


class TestSiteContent:
    def test_defaults(self):
        s = SiteContent()
        assert s.text == ""
        assert s.headings == []
        assert s.pages_fetched == 0

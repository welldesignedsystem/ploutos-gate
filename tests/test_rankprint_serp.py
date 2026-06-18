import os
from unittest.mock import MagicMock, patch

import pytest

from rankprint.serp import DuckDuckGoChecker, TavilyChecker


def _mock_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


@pytest.mark.asyncio
async def test_search_returns_results():
    html = """
    <html>
    <body>
    <div class="result">
      <h2 class="result__title">
        <a class="result__a" href="https://example.com/page1">Result One</a>
      </h2>
      <a class="result__snippet" href="https://example.com/page1">Snippet for one</a>
    </div>
    <div class="result">
      <h2 class="result__title">
        <a class="result__a" href="https://other.com/page2">Result Two</a>
      </h2>
      <a class="result__snippet" href="https://other.com/page2">Snippet for two</a>
    </div>
    </body>
    </html>
    """
    checker = DuckDuckGoChecker()
    checker._delay = 0

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = _mock_response(html)

        results = await checker.search("test query")
        assert len(results) == 2
        assert results[0]["title"] == "Result One"
        assert results[0]["url"] == "https://example.com/page1"
        assert results[0]["domain"] == "example.com"
        assert results[0]["snippet"] == "Snippet for one"
        assert results[1]["title"] == "Result Two"


@pytest.mark.asyncio
async def test_search_respects_num_results():
    html = (
        "<html><body>"
        '<div class="result"><h2 class="result__title">'
        '<a class="result__a" href="https://a.com">A</a></h2>'
        '<a class="result__snippet">a</a></div>'
        '<div class="result"><h2 class="result__title">'
        '<a class="result__a" href="https://b.com">B</a></h2>'
        '<a class="result__snippet">b</a></div>'
        '<div class="result"><h2 class="result__title">'
        '<a class="result__a" href="https://c.com">C</a></h2>'
        '<a class="result__snippet">c</a></div>'
        "</body></html>"
    )
    checker = DuckDuckGoChecker()
    checker._delay = 0

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = _mock_response(html)

        results = await checker.search("test", num_results=2)
        assert len(results) == 2


@pytest.mark.asyncio
async def test_search_network_error():
    checker = DuckDuckGoChecker()
    checker._delay = 0

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = Exception("Network error")
        results = await checker.search("test")
        assert results == []


@pytest.mark.asyncio
async def test_search_empty_page():
    html = "<html><body></body></html>"
    checker = DuckDuckGoChecker()
    checker._delay = 0

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = _mock_response(html)

        results = await checker.search("test")
        assert results == []


class TestTavilyChecker:
    def _mock_json_response(self, data: dict) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = data
        return resp

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        checker = TavilyChecker(api_key="test-key")
        data = {
            "results": [
                {
                    "title": "Result One",
                    "url": "https://example.com/page1",
                    "content": "Snippet one",
                },
                {
                    "title": "Result Two",
                    "url": "https://other.com/page2",
                    "content": "Snippet two",
                },
            ],
        }
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = self._mock_json_response(data)

            results = await checker.search("test query")
            assert len(results) == 2
            assert results[0]["title"] == "Result One"
            assert results[0]["url"] == "https://example.com/page1"
            assert results[0]["domain"] == "example.com"
            assert results[0]["snippet"] == "Snippet one"
            assert results[1]["title"] == "Result Two"

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        checker = TavilyChecker(api_key="test-key")
        data = {"results": []}
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = self._mock_json_response(data)

            results = await checker.search("test")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_network_error(self):
        checker = TavilyChecker(api_key="test-key")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = Exception("API error")
            results = await checker.search("test")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        os.environ.pop("TAVILY_API_KEY", None)
        checker = TavilyChecker()
        data = {"results": [{"title": "T", "url": "https://x.com", "content": "c"}]}
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = self._mock_json_response(data)
            results = await checker.search("test")
            assert len(results) == 1

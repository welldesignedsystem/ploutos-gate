from unittest.mock import MagicMock, patch

import pytest

from rankprint.crawler import extract_domain, fetch_page_text


def _mock_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


def test_extract_domain():
    assert extract_domain("https://www.example.com/page") == "www.example.com"
    assert extract_domain("http://example.com") == "example.com"
    assert extract_domain("not-a-url") == "not-a-url"


@pytest.mark.asyncio
async def test_fetch_page_text_success():
    html = "<html><body><p>Hello world</p></body></html>"
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = _mock_response(html)

        result = await fetch_page_text("https://example.com")
        assert result is not None
        assert "Hello world" in result


@pytest.mark.asyncio
async def test_fetch_page_text_strips_tags():
    html = (
        "<html><body>"
        "<p>Main content</p>"
        "<script>alert('bad')</script>"
        "<style>.css{}</style>"
        "<nav>nav stuff</nav>"
        "</body></html>"
    )
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = _mock_response(html)

        result = await fetch_page_text("https://example.com")
        assert result is not None
        assert "Main content" in result
        assert "alert" not in result
        assert ".css" not in result
        assert "nav stuff" not in result


@pytest.mark.asyncio
async def test_fetch_page_text_network_error():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")
        result = await fetch_page_text("https://example.com")
        assert result is None

import asyncio
import os
import time
from typing import cast
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag


class DuckDuckGoChecker:
    def __init__(self) -> None:
        self._delay = float(os.getenv("RANKPRINT_SERP_DELAY", "3"))
        self._last_call = 0.0

    async def search(self, query: str, num_results: int = 10) -> list[dict[str, str]]:
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self._delay:
            await asyncio.sleep(self._delay - elapsed)
        self._last_call = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query},
                    headers={"User-Agent": "ploutos-gate/1.0"},
                )
                resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        results: list[dict[str, str]] = []

        for article in soup.select("div.result"):
            link_el = article.select_one(".result__a")
            if not isinstance(link_el, Tag):
                continue
            title = link_el.get_text(strip=True)
            href = cast(str, link_el.get("href", ""))
            snippet_el = article.select_one(".result__snippet")
            snippet = snippet_el.get_text(strip=True) if isinstance(snippet_el, Tag) else ""
            results.append(
                {
                    "title": title,
                    "url": href,
                    "domain": urlparse(href).hostname or href,
                    "snippet": snippet,
                }
            )

        return results[:num_results]


class TavilyChecker:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self._last_call = 0.0

    async def search(self, query: str, num_results: int = 10) -> list[dict[str, str]]:
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        self._last_call = time.time()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self._api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": num_results,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []

        results: list[dict[str, str]] = []
        for item in data.get("results", []):
            url = item.get("url", "")
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": url,
                    "domain": urlparse(url).hostname or url,
                    "snippet": item.get("content", ""),
                }
            )
        return results

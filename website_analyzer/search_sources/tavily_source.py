import os

from tavily import TavilyClient

from website_analyzer.models import CompetitorResult
from website_analyzer.search_sources.base import SearchSource


class TavilySearchSource(SearchSource):
    @property
    def name(self) -> str:
        return "tavily"

    async def search(self, query: str, max_results: int = 5) -> list[CompetitorResult]:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return []

        try:
            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, max_results=max_results)
            results = response.get("results", [])
            return [
                CompetitorResult(
                    name=_extract_company_name(r.get("content", ""), r.get("url", "")),
                    domain=_extract_domain(r.get("url", "")),
                    description=r.get("content", "")[:300],
                    source=self.name,
                )
                for r in results
                if r.get("url")
            ]
        except Exception:
            return []


def _extract_domain(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return url


def _extract_company_name(content: str, url: str) -> str:
    domain = _extract_domain(url)
    return domain.removesuffix(".com").removesuffix(".io").removesuffix(".org").split(".")[-1].title() if domain else url

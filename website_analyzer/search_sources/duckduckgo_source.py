from urllib.parse import urlparse

from ddgs import DDGS

from website_analyzer.models import CompetitorResult
from website_analyzer.search_sources.base import SearchSource


class DuckDuckGoSearchSource(SearchSource):
    @property
    def name(self) -> str:
        return "duckduckgo"

    async def search(self, query: str, max_results: int = 5) -> list[CompetitorResult]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                CompetitorResult(
                    name=_extract_company_name(r.get("title", ""), r.get("href", "")),
                    domain=_extract_domain(r.get("href", "")),
                    description=r.get("body", "")[:300],
                    source=self.name,
                )
                for r in results
                if r.get("href")
            ]
        except Exception:
            return []


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return url


def _extract_company_name(title: str, url: str) -> str:
    if title and " - " in title:
        return title.split(" - ")[0].strip()
    if title:
        return title.strip()
    domain = _extract_domain(url)
    return domain.removesuffix(".com").removesuffix(".io").removesuffix(".org").split(".")[-1].title() if domain else url

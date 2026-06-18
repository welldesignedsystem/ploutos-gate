from typing import cast
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag


class SiteContent:
    def __init__(self) -> None:
        self.text: str = ""
        self.headings: list[str] = []
        self.pages_fetched: int = 0


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url, headers={"User-Agent": "ploutos-gate/1.0"})
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


async def fetch_site(url: str, max_pages: int = 10) -> SiteContent:
    result = SiteContent()
    domain = urlparse(url).hostname or ""
    visited: set[str] = set()
    to_fetch: list[str] = [url]

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        while to_fetch and len(visited) < max_pages:
            page_url = to_fetch.pop(0)
            if page_url in visited:
                continue
            visited.add(page_url)

            html = await _fetch_page(client, page_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")

            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            for h in soup.find_all(["h1", "h2", "h3"]):
                text = h.get_text(strip=True)
                if text and len(text) > 2:
                    result.headings.append(text)

            text = soup.get_text(separator=" ", strip=True)
            if result.text:
                result.text += "\n\n"
            result.text += text[:5000]
            result.pages_fetched += 1

            if result.pages_fetched == 1:
                for a in soup.find_all("a", href=True):
                    if not isinstance(a, Tag):
                        continue
                    href = cast(str, a.get("href", ""))
                    if not href:
                        continue
                    full = urljoin(page_url, href)
                    parsed = urlparse(full)
                    if parsed.hostname == domain and parsed.scheme in ("http", "https"):
                        clean = parsed._replace(fragment="").geturl()
                        if clean not in visited and clean not in to_fetch:
                            to_fetch.append(clean)

    return result


def extract_domain(url: str) -> str:
    return urlparse(url).hostname or url

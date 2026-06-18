from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


async def fetch_page_text(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ploutos-gate/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text[:10000]
    except Exception:
        return None


def extract_domain(url: str) -> str:
    return urlparse(url).hostname or url

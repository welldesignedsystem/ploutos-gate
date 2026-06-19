import asyncio

from website_analyzer.models import CompetitorGroup, CompetitorSelection
from website_analyzer.search_sources import get_source, list_sources


def _build_queries(sel: CompetitorSelection) -> list[str]:
    parts = []
    if sel.products:
        parts.append(" ".join(sel.products))
    if sel.categories:
        parts.append(" ".join(sel.categories))
    if sel.terms:
        parts.append(" ".join(sel.terms))
    if sel.audience:
        parts.append(" ".join(sel.audience))

    base = " ".join(parts) if parts else ""
    if not base:
        return []

    return [
        f"{base} companies",
        f"top {base} providers",
    ]


def _deduplicate(results: list) -> list:
    seen: set[str] = set()
    out = []
    for r in results:
        key = r.domain.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


async def search_competitors(
    selections: list[CompetitorSelection],
    sources: list[str] | None = None,
    max_results: int = 5,
) -> list[CompetitorGroup]:
    if sources is None:
        sources = list_sources()
    else:
        sources = [s for s in sources if s in list_sources()]

    if not sources:
        return []

    groups: list[CompetitorGroup] = []
    for sel in selections:
        queries = _build_queries(sel)
        if not queries:
            groups.append(CompetitorGroup(selection=sel, companies=[]))
            continue

        all_results = []
        for query in queries:
            for source_name in sources:
                try:
                    source = get_source(source_name)
                    results = await source.search(query, max_results=max_results)
                    all_results.extend(results)
                except Exception:
                    continue

        deduped = _deduplicate(all_results)
        groups.append(CompetitorGroup(selection=sel, companies=deduped[:max_results]))

    return groups

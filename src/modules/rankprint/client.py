import json
import os
from typing import Any, cast
from urllib.parse import urlparse

from llm.client import structured_chat
from llm.models import LLMConfig

from .crawler import extract_domain, fetch_page_text
from .models import (
    BusinessProfile,
    CompanyScanOutput,
    GeneratedSearchQuery,
    ProviderResult,
    QueryResult,
    RankedReference,
    ScanSummary,
    SearchSurface,
    SkippedProvider,
    TextReference,
)
from .serp import DuckDuckGoChecker, TavilyChecker


def _domain_matches(result_domain: str, target_domain: str) -> bool:
    rd = result_domain.lower().removeprefix("www.")
    td = target_domain.lower().removeprefix("www.")
    return rd == td or rd.endswith("." + td)


async def _extract_profile(
    url: str,
    domain: str,
    page_text: str | None,
    config: LLMConfig,
) -> BusinessProfile | None:
    if not page_text:
        return None
    schema = json.dumps(BusinessProfile.model_json_schema(), indent=2)
    system = (
        "You are a business analyst. Extract a structured business profile "
        "from the website text below. Return only valid JSON that matches "
        "the given schema. Do NOT wrap in markdown code blocks."
    )
    user = f"Website URL: {url}\n\nWebsite text:\n{page_text[:8000]}\n\nSchema:\n{schema}"
    try:
        result = await structured_chat(system, user, BusinessProfile, config)
        if result is None:
            return None
        profile = cast(BusinessProfile, result)
        profile.url = url
        profile.domain = domain
        return profile
    except Exception:
        return None


async def _generate_queries(
    profile: BusinessProfile | None,
    terms: list[str],
    config: LLMConfig,
    max_queries: int = 10,
) -> list[GeneratedSearchQuery]:
    schema = json.dumps(
        {"type": "array", "items": GeneratedSearchQuery.model_json_schema()},
        indent=2,
    )
    profile_text = (
        f"Name: {profile.name}\n"
        f"Description: {profile.description}\n"
        f"Products: {', '.join(profile.products)}\n"
        f"Audiences: {', '.join(profile.audiences)}\n"
        f"Categories: {', '.join(profile.categories)}"
        if profile
        else "No profile available."
    )
    system = (
        f"You are an SEO strategist. Given a business profile and seed search terms, "
        f"generate up to {max_queries} relevant search queries to evaluate whether "
        f"this company appears in search results. For each query specify intent "
        f"(informational, commercial, transactional, navigational) and surface "
        f"(seo, aeo, geo). Return only valid JSON matching the schema. "
        f"Do NOT wrap in markdown code blocks."
    )
    user = f"Business Profile:\n{profile_text}\n\nSeed Terms:\n{', '.join(terms)}\n\nSchema:\n{schema}"
    try:
        result = await structured_chat(
            system,
            user,
            list[GeneratedSearchQuery],
            config,
        )
        if result and len(result) > 0:
            return cast(list[GeneratedSearchQuery], result)[:max_queries]
    except Exception:
        pass

    seeds = (
        terms[:max_queries]
        if terms
        else ([profile.name] if profile and profile.name else [profile.domain] if profile else [])
    )
    if not seeds:
        return []
    return [
        GeneratedSearchQuery(
            query=s,
            intent="informational",
            surface="seo",
            reason=f"Seed: {s}",
        )
        for s in seeds
    ]


def _ranked_ref(
    rank: int,
    title: str,
    url_str: str,
    domain: str,
    snippet: str,
    relevance: str,
) -> RankedReference:
    parsed = urlparse(url_str)
    valid_url = url_str if parsed.scheme and parsed.netloc else None
    return RankedReference(
        rank=rank,
        title=title,
        url=valid_url,
        domain=domain,
        text_reference=TextReference(
            source="snippet",
            text=snippet,
            relevance=relevance,
        ),
    )


def _search_providers() -> tuple[list[tuple[str, SearchSurface, Any]], list[SkippedProvider]]:
    providers: list[tuple[str, SearchSurface, Any]] = [
        ("duckduckgo", "seo", DuckDuckGoChecker()),
    ]
    skipped: list[SkippedProvider] = []
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_key:
        providers.append(("tavily", "seo", TavilyChecker(tavily_key)))
    else:
        skipped.append(SkippedProvider(provider="tavily", reason="Missing TAVILY_API_KEY"))
    return providers, skipped


async def _run_provider(
    provider_name: str,
    surface: SearchSurface,
    checker: Any,
    query: str,
    domain: str,
    results_per_query: int = 10,
) -> ProviderResult:
    results = await checker.search(query, num_results=results_per_query)
    matches: list[RankedReference] = []
    competitors: list[RankedReference] = []
    best_rank: int | None = None

    for rank, result in enumerate(results, start=1):
        result_domain = result.get("domain", "")
        ref = _ranked_ref(
            rank=rank,
            title=result.get("title", ""),
            url_str=result.get("url", ""),
            domain=result_domain,
            snippet=result.get("snippet", ""),
            relevance="",
        )
        if _domain_matches(result_domain, domain):
            matches.append(ref)
            if best_rank is None or rank < best_rank:
                best_rank = rank
        else:
            competitors.append(ref)

    return ProviderResult(
        provider=provider_name,
        surface=surface,
        found=best_rank is not None,
        best_rank=best_rank,
        matches=matches,
        competitors=competitors,
    )


async def scan(
    url: str,
    terms: list[str],
    max_queries: int = 10,
    results_per_query: int = 10,
) -> CompanyScanOutput:
    config = LLMConfig.from_env()
    domain = extract_domain(url)

    page_text = await fetch_page_text(url)
    profile = await _extract_profile(url, domain, page_text, config)
    queries = await _generate_queries(profile, terms, config, max_queries)

    providers, skipped_providers = _search_providers()

    query_results: list[QueryResult] = []
    total_checks = 0
    checks_found = 0
    all_best_ranks: list[int] = []

    for q in queries:
        provider_results: list[ProviderResult] = []
        for provider_name, surface, checker in providers:
            pr = await _run_provider(provider_name, surface, checker, q.query, domain, results_per_query)
            provider_results.append(pr)
            total_checks += 1
            if pr.found and pr.best_rank is not None:
                checks_found += 1
                all_best_ranks.append(pr.best_rank)

        query_results.append(
            QueryResult(
                query=q.query,
                intent=q.intent,
                surface=q.surface,
                reason=q.reason,
                provider_results=provider_results,
            )
        )

    avg_best = round(sum(all_best_ranks) / len(all_best_ranks), 1) if all_best_ranks else None

    summary = ScanSummary(
        queries_generated=len(queries),
        providers_run=len(providers),
        providers_skipped=len(skipped_providers),
        total_checks=total_checks,
        checks_found=checks_found,
        best_rank=min(all_best_ranks) if all_best_ranks else None,
        average_best_rank=avg_best,
        visibility_score=round((checks_found / total_checks) * 100) if total_checks else 0,
    )

    return CompanyScanOutput(
        company=profile or BusinessProfile(url=url, domain=domain),
        query_results=query_results,
        skipped_providers=skipped_providers,
        summary=summary,
    )

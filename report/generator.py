from langchain_core.prompts import ChatPromptTemplate

from common.models import CompanyProfile
from report.models import PlatformReport, ReportOutput
from website_analyzer.llm import build_llm
from website_analyzer.search_sources import get_source, list_sources


SYSTEM_TEMPLATE = """You are a digital compliance analyst. Evaluate the given company against {dimension} best practices.

Use the crawled website text, the company profile, and the search results as evidence.

Return:
- readiness_score: integer 0–100
- reasoning: concise paragraph summarizing how well the company performs
- recommendations: up to 5 specific, actionable steps to improve

Be honest and critical — score based on actual evidence, not generic praise."""

HUMAN_TEMPLATE = """Dimension: {dimension}
Company: {company_name} ({domain_url})
Industry: {business_domain}
Products: {products}
Audience: {audience}
Categories: {categories}
Keywords: {terms}

Website content:
{crawl_content}

Web search results for {dimension} context:
{search_context}"""

DIMENSIONS = ["SEO", "GEO", "AEO"]


async def _search_for_dimension(dimension: str, profile: CompanyProfile, max_results: int = 5) -> str:
    terms = " ".join((profile.terms or [])[:3]) if profile.terms else ""
    domain = profile.business_domain or ""
    dimension_queries = {
        "SEO": [
            f"SEO best practices {domain} {terms} 2026",
            f"technical SEO checklist {domain} website optimization 2026",
        ],
        "GEO": [
            f"generative engine optimization GEO best practices {domain} 2026",
            f"LLM search optimization {domain} AI overviews 2026",
        ],
        "AEO": [
            f"answer engine optimization AEO featured snippets {domain} 2026",
            f"voice search optimization conversational AI {domain} 2026",
        ],
    }
    queries = dimension_queries.get(dimension, [f"{domain} {terms} compliance best practices 2026"])
    source = get_source("tavily") if "tavily" in list_sources() else get_source("duckduckgo")
    all_snippets = []
    for q in queries:
        try:
            results = await source.search(q, max_results=max_results)
            for r in results:
                if r.description.strip():
                    all_snippets.append(r.description[:300])
        except Exception:
            continue
    if not all_snippets:
        return "No search results available."
    return "\n".join(f"- {s}" for s in all_snippets[:8])


async def generate_report(
    profile: CompanyProfile,
    crawl_content: str,
) -> ReportOutput:
    llm = build_llm()
    platform_reports = []

    for dim in DIMENSIONS:
        search_context = await _search_for_dimension(dim, profile)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_TEMPLATE),
            ("human", HUMAN_TEMPLATE),
        ])
        structured_llm = llm.with_structured_output(PlatformReport)
        chain = prompt | structured_llm
        report = await chain.ainvoke({
            "dimension": dim,
            "company_name": profile.company_name,
            "domain_url": profile.domain_url,
            "business_domain": profile.business_domain or "N/A",
            "products": ", ".join(profile.products or []),
            "audience": ", ".join(profile.audience or []),
            "categories": ", ".join(profile.categories or []),
            "terms": ", ".join(profile.terms or []),
            "crawl_content": crawl_content[:12000] if crawl_content else "No content available.",
            "search_context": search_context,
        })
        report.platform = dim
        platform_reports.append(report)

    overall = round(sum(p.readiness_score for p in platform_reports) / len(platform_reports), 1) if platform_reports else 0

    all_recs = []
    for p in platform_reports:
        for r in p.recommendations[:2]:
            all_recs.append(f"[{p.platform}] {r}")

    return ReportOutput(
        company_name=profile.company_name,
        domain_url=profile.domain_url,
        platforms=platform_reports,
        summary_action_plan=all_recs[:5],
    )

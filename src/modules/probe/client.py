import json
from typing import cast

from llm.client import structured_chat
from llm.models import LLMConfig

from .crawler import SiteContent, extract_domain, fetch_site
from .models import BusinessProfile, GeneratedTerm, ProbeOutput


async def probe(
    url: str,
    max_terms: int = 20,
) -> ProbeOutput:
    config = LLMConfig.from_env()
    domain = extract_domain(url)

    site = await fetch_site(url, max_pages=10)

    profile = await _extract_profile(url, domain, site, config)
    terms = await _generate_terms(profile, site, config, max_terms)

    return ProbeOutput(
        url=url,
        max_terms=max_terms,
        target=profile or BusinessProfile(url=url, domain=domain),
        terms=terms,
    )


async def _extract_profile(
    url: str,
    domain: str,
    site: SiteContent,
    config: LLMConfig,
) -> BusinessProfile | None:
    if not site.text and not site.headings:
        return None

    schema = json.dumps(BusinessProfile.model_json_schema(), indent=2)
    text = site.text[:8000] if site.text else ""
    headings = "\n".join(site.headings[:30])

    system = (
        "You are a business analyst. Extract a structured business profile "
        "from the website text and page headings below. "
        "Return only valid JSON that matches the given schema. "
        "Do NOT wrap in markdown code blocks."
    )
    user = f"Website URL: {url}\n\nPage headings:\n{headings}\n\nWebsite text:\n{text}\n\nSchema:\n{schema}"

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


async def _generate_terms(
    profile: BusinessProfile | None,
    site: SiteContent,
    config: LLMConfig,
    max_terms: int = 20,
) -> list[GeneratedTerm]:
    schema = json.dumps(
        {"type": "array", "items": GeneratedTerm.model_json_schema()},
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
        f"You are a competitive analyst. Read the business profile and "
        f"website content below. Understand what this business offers — "
        f"its products, services, industries, and audiences. Then generate "
        f"up to {max_terms} search terms or combinations of terms that "
        f"would surface this company's direct competitors. "
        f"Think about: service categories, industry verticals, product types, "
        f"alternative names for what they do, and related service areas. "
        f"For each term, explain why it was chosen and what type of competitor "
        f"it would uncover. "
        f"Return only valid JSON matching the schema. "
        f"Do NOT wrap in markdown code blocks."
    )

    headings = "\n".join(site.headings[:30]) if site.headings else ""
    text = site.text[:5000] if site.text else ""
    user = (
        f"Business Profile:\n{profile_text}\n\n"
        f"Website headings:\n{headings}\n\n"
        f"Website text:\n{text}\n\n"
        f"Schema:\n{schema}"
    )

    try:
        result = await structured_chat(system, user, list[GeneratedTerm], config)
        if result and len(result) > 0:
            return cast(list[GeneratedTerm], result)[:max_terms]
    except Exception:
        pass

    return _fallback_terms(site, profile, max_terms)


_UI_HEADING_PATTERNS = {
    "how", "why", "what", "where", "when", "who",
    "our", "about", "contact", "faq", "faqs",
    "testimonial", "testimonials", "review", "reviews",
    "blog", "career", "careers",
    "meet", "meet the", "get in touch", "get started",
    "popular", "subscribe", "join", "follow",
    "resources", "support", "help",
}


def _is_service_heading(heading: str) -> bool:
    text = heading.strip().lower().rstrip("?")
    words = text.split()

    if len(words) < 2 or len(words) > 8:
        return False

    first_word = words[0].rstrip("?")
    if first_word in _UI_HEADING_PATTERNS:
        return False

    for w in words:
        if w in ("aboutus", "contactus"):
            return False

    whole = text.replace(" ", "")
    for pat in ("aboutus", "contactus", "getintouch", "faq", "subscribe"):
        if pat in whole:
            return False

    return True


def _fallback_terms(
    site: SiteContent,
    profile: BusinessProfile | None,
    max_terms: int = 20,
) -> list[GeneratedTerm]:
    seen: set[str] = set()
    terms: list[GeneratedTerm] = []

    if profile and profile.name and profile.name.lower() not in seen:
        seen.add(str(profile.name).lower())
        terms.append(
            GeneratedTerm(
                terms=profile.name,
                reason="Company name — core business identifier",
            )
        )

    if profile and profile.categories:
        for cat in profile.categories:
            normalized = cat.strip().lower()
            if normalized not in seen and normalized:
                seen.add(normalized)
                terms.append(
                    GeneratedTerm(
                        terms=cat.strip(),
                        reason="Business category from profile",
                    )
                )
                if len(terms) >= max_terms:
                    return terms

    for h in site.headings:
        stripped = h.strip()
        normalized = stripped.lower()
        if (
            normalized not in seen
            and stripped
            and _is_service_heading(stripped)
        ):
            seen.add(normalized)
            terms.append(
                GeneratedTerm(
                    terms=stripped,
                    reason="Page heading describing a service or offering",
                )
            )
            if len(terms) >= max_terms:
                return terms

    if profile and profile.domain and profile.domain.lower() not in seen:
        readable = str(profile.domain).replace("www.", "")
        terms.append(
            GeneratedTerm(
                terms=readable,
                reason="Domain-based fallback term",
            )
        )

    return terms[:max_terms]

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    company_name: str = Field(description="Name of the company")
    domain_url: str = Field(description="Domain URL of the company website")
    business_domain: str = Field(description="Business domain / industry the company operates in")
    products: list[str] = Field(description="Products or services offered by the company")
    audience: list[str] = Field(description="Target audience or customer segments")
    categories: list[str] = Field(description="Business categories the company falls under")
    terms: list[str] = Field(description="Relevant terms or term combinations related to the business")


class SearchQuery(BaseModel):
    query: str = Field(description="A search query designed to find information about this company")
    reason: str = Field(description="Why this query is relevant to finding information about this company")


class SearchQueryList(BaseModel):
    queries: list[SearchQuery] = Field(description="List of search queries with reasons")


class CompetitorSelection(BaseModel):
    audience: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)


class CompetitorResult(BaseModel):
    name: str
    domain: str
    description: str
    source: str


class CompetitorGroup(BaseModel):
    selection: CompetitorSelection
    companies: list[CompetitorResult]

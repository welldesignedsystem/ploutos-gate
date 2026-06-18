from pydantic import BaseModel, Field, HttpUrl


class BusinessProfile(BaseModel):
    url: str
    domain: str
    name: str | None = None
    description: str | None = None
    products: list[str] = Field(default_factory=list)
    audiences: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class ProbeRequest(BaseModel):
    url: HttpUrl
    max_terms: int = Field(default=20, ge=1, le=50)


class GeneratedTerm(BaseModel):
    terms: str
    reason: str


class ProbeOutput(BaseModel):
    url: str
    max_terms: int
    target: BusinessProfile
    terms: list[GeneratedTerm]

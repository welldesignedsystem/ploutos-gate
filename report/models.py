from datetime import datetime, timezone
from pydantic import BaseModel, Field


class PlatformReport(BaseModel):
    platform: str = Field(description="Dimension name: SEO, GEO, or AEO")
    readiness_score: int = Field(ge=0, le=100, description="Score 0–100")
    reasoning: str = Field(description="Summary assessment for this dimension")
    recommendations: list[str] = Field(description="Actionable recommendations")


class ReportOutput(BaseModel):
    company_name: str
    domain_url: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    platforms: list[PlatformReport]
    summary_action_plan: list[str]

from pydantic import BaseModel, Field


class AnalysisBase(BaseModel):
    subreddits: str = Field(default="all", description="Comma-separated subreddit names")
    time_filter: str = Field(default="month", description="Time filter: hour, day, week, month, year, all")
    limit: int = Field(default=50, ge=1, le=100, description="Max posts to analyze")


class KeywordDiscovery(AnalysisBase):
    topic: str = Field(description="Topic to discover keywords for")
    max_keywords: int = Field(default=20, ge=1, le=100, description="Max keywords to return")


class IntentAnalysis(AnalysisBase):
    query: str = Field(description="Search query to analyze intent for")


class ContentGapAnalysis(AnalysisBase):
    topic: str = Field(description="Topic to find content gaps in")


class TrendDetection(AnalysisBase):
    subreddit: str = Field(description="Subreddit to detect trends in")
    lookback_days: int = Field(default=7, ge=1, le=90, description="Days to look back")


class CompetitorResearch(AnalysisBase):
    topic: str = Field(description="Topic to research competitors for")


class BacklinkProspecting(AnalysisBase):
    topic: str = Field(description="Topic to find backlink opportunities in")


class SERPTargeting(AnalysisBase):
    query: str = Field(description="Query to analyze SERP patterns for")


class AudienceLanguage(AnalysisBase):
    topic: str = Field(description="Topic to extract audience language for")

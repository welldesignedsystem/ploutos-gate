import pydantic
import pytest

from reddit.analyze.models import (
    AnalysisBase,
    AudienceLanguage,
    BacklinkProspecting,
    CompetitorResearch,
    ContentGapAnalysis,
    IntentAnalysis,
    KeywordDiscovery,
    SERPTargeting,
    TrendDetection,
)


def test_analysis_base_defaults():
    m = AnalysisBase()
    assert m.subreddits == "all"
    assert m.time_filter == "month"
    assert m.limit == 50


def test_analysis_base_limit_clamped():
    with pytest.raises(pydantic.ValidationError):
        AnalysisBase(limit=0)
    with pytest.raises(pydantic.ValidationError):
        AnalysisBase(limit=101)


def test_keyword_discovery():
    m = KeywordDiscovery(topic="python web frameworks")
    assert m.topic == "python web frameworks"
    assert m.max_keywords == 20


def test_keyword_discovery_max_keywords_clamped():
    with pytest.raises(pydantic.ValidationError):
        KeywordDiscovery(topic="test", max_keywords=0)
    with pytest.raises(pydantic.ValidationError):
        KeywordDiscovery(topic="test", max_keywords=101)


def test_intent_analysis():
    m = IntentAnalysis(query="best laptop for programming")
    assert m.query == "best laptop for programming"


def test_content_gaps():
    m = ContentGapAnalysis(topic="machine learning")
    assert m.topic == "machine learning"


def test_trend_detection():
    m = TrendDetection(subreddit="python", lookback_days=14)
    assert m.subreddit == "python"
    assert m.lookback_days == 14


def test_trend_detection_lookback_clamped():
    with pytest.raises(pydantic.ValidationError):
        TrendDetection(subreddit="python", lookback_days=0)
    with pytest.raises(pydantic.ValidationError):
        TrendDetection(subreddit="python", lookback_days=91)


def test_trend_detection_default():
    m = TrendDetection(subreddit="python")
    assert m.lookback_days == 7


def test_competitor_research():
    m = CompetitorResearch(topic="kubernetes")
    assert m.topic == "kubernetes"


def test_backlink_prospecting():
    m = BacklinkProspecting(topic="web dev tools")
    assert m.topic == "web dev tools"


def test_serp_targeting():
    m = SERPTargeting(query="best IDE 2026")
    assert m.query == "best IDE 2026"


def test_audience_language():
    m = AudienceLanguage(topic="rust vs go")
    assert m.topic == "rust vs go"


def test_all_models_inherit_analysis_base():
    for model_cls in [
        AudienceLanguage,
        BacklinkProspecting,
        CompetitorResearch,
        ContentGapAnalysis,
        IntentAnalysis,
        KeywordDiscovery,
        SERPTargeting,
        TrendDetection,
    ]:
        assert issubclass(model_cls, AnalysisBase)

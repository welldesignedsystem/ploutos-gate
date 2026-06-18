import pytest
from pydantic import ValidationError

from probe.models import BusinessProfile, GeneratedTerm, ProbeOutput, ProbeRequest


class TestProbeRequest:
    def test_valid(self):
        r = ProbeRequest(url="https://example.com", max_terms=15)
        assert str(r.url) == "https://example.com/"
        assert r.max_terms == 15

    def test_default_max_terms(self):
        r = ProbeRequest(url="https://example.com")
        assert r.max_terms == 20

    def test_max_terms_clamped_low(self):
        with pytest.raises(ValidationError):
            ProbeRequest(url="https://example.com", max_terms=0)

    def test_max_terms_clamped_high(self):
        with pytest.raises(ValidationError):
            ProbeRequest(url="https://example.com", max_terms=51)

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            ProbeRequest(url="not-a-url")


class TestGeneratedTerm:
    def test_valid(self):
        t = GeneratedTerm(terms="best crm software", reason="finds CRM competitors")
        assert t.terms == "best crm software"
        assert t.reason == "finds CRM competitors"

    def test_defaults(self):
        t = GeneratedTerm(terms="test", reason="reason")
        assert t.terms == "test"


class TestProbeOutput:
    def test_valid(self):
        profile = BusinessProfile(url="https://ex.com", domain="ex.com", name="Ex Corp")
        terms = [
            GeneratedTerm(terms="ex competitor", reason="finds direct competitors"),
        ]
        out = ProbeOutput(url="https://ex.com", max_terms=20, target=profile, terms=terms)
        assert out.url == "https://ex.com"
        assert out.max_terms == 20
        assert out.target.name == "Ex Corp"
        assert len(out.terms) == 1
        assert out.terms[0].terms == "ex competitor"

    def test_empty_terms(self):
        profile = BusinessProfile(url="https://ex.com", domain="ex.com")
        out = ProbeOutput(url="https://ex.com", max_terms=10, target=profile, terms=[])
        assert out.terms == []

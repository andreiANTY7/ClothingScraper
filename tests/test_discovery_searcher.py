import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discovery.searcher import (
    _extract_domain, filter_known_sites, search_candidate_sites
)


def test_extract_domain_valid_url():
    assert _extract_domain("https://www.example.com/catalog/men") == "https://www.example.com"


def test_extract_domain_no_path():
    assert _extract_domain("https://shop.example.com") == "https://shop.example.com"


def test_extract_domain_invalid_returns_none():
    assert _extract_domain("not a url") is None


def test_filter_known_sites_removes_exact_match():
    candidates = ["https://known.com", "https://new-site.com"]
    known = {"https://known.com", "https://other-known.com"}
    result = filter_known_sites(candidates, known)
    assert result == ["https://new-site.com"]


def test_filter_known_sites_removes_subdomain_match():
    candidates = ["https://www.btobturk.com"]
    known = {"https://www.btobturk.com"}
    result = filter_known_sites(candidates, known)
    assert result == []


def test_filter_known_sites_empty_known():
    candidates = ["https://a.com", "https://b.com"]
    result = filter_known_sites(candidates, set())
    assert set(result) == {"https://a.com", "https://b.com"}


def test_filter_known_sites_no_false_positive_on_partial_domain():
    # "a.com" should NOT block "abc.com" — only true subdomain/exact matches should block
    candidates = ["https://abc.com"]
    known = {"https://a.com"}
    result = filter_known_sites(candidates, known)
    assert result == ["https://abc.com"]


def test_search_candidate_sites_calls_ddgs(mocker):
    mock_ddgs_instance = mocker.MagicMock()
    mock_ddgs_instance.__enter__ = mocker.MagicMock(return_value=mock_ddgs_instance)
    mock_ddgs_instance.__exit__ = mocker.MagicMock(return_value=False)
    mock_ddgs_instance.text.return_value = [
        {"href": "https://wholesale-site.com/catalog", "title": "Wholesale", "body": "B2B"},
        {"href": "https://another-b2b.com/men", "title": "B2B Clothing", "body": "Wholesale"},
    ]
    mocker.patch("discovery.searcher.DDGS", return_value=mock_ddgs_instance)

    results = search_candidate_sites(max_results=5)
    assert "https://wholesale-site.com" in results
    assert "https://another-b2b.com" in results


def test_search_candidate_sites_deduplicates(mocker):
    mock_ddgs_instance = mocker.MagicMock()
    mock_ddgs_instance.__enter__ = mocker.MagicMock(return_value=mock_ddgs_instance)
    mock_ddgs_instance.__exit__ = mocker.MagicMock(return_value=False)
    mock_ddgs_instance.text.return_value = [
        {"href": "https://same-site.com/page1", "title": "A", "body": "B"},
        {"href": "https://same-site.com/page2", "title": "A", "body": "B"},
    ]
    mocker.patch("discovery.searcher.DDGS", return_value=mock_ddgs_instance)

    results = search_candidate_sites(max_results=5)
    assert results.count("https://same-site.com") == 1

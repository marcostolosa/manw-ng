import pytest

from manw_ng.core.scraper import Win32APIScraper


def test_scraper_basic_functionality():
    """Test basic scraper functionality instead of deprecated modules"""
    scraper = Win32APIScraper()
    # Test that scraper can be initialized
    assert scraper.language == "us"
    assert scraper.base_url == "https://learn.microsoft.com/en-us"

    # Test language switching
    br_scraper = Win32APIScraper(language="br")
    assert br_scraper.language == "br"
    assert br_scraper.base_url == "https://learn.microsoft.com/pt-br"


def test_url_format_display():
    """Test URL formatting functionality"""
    scraper = Win32APIScraper()
    url = "https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew"
    formatted = scraper._format_url_display(url)
    assert "api/fileapi/nf-fileapi-createfilew" in formatted


def test_direct_url_mapping():
    """Test direct URL mapping functionality"""
    scraper = Win32APIScraper()
    direct_url = scraper._try_direct_url("CreateFileW")
    # Should return a URL or None, not crash
    assert direct_url is None or isinstance(direct_url, str)

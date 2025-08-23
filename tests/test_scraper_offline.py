import pathlib
from manw_ng.core.scraper import Win32APIScraper
from manw_ng.utils.complete_win32_api_mapping import get_function_url
from manw_ng.utils.http_client import HTTPClient

FIXTURE_DIR = pathlib.Path(__file__).with_name("fixtures")


def load_fixture(name: str) -> str:
    return (FIXTURE_DIR / f"{name.lower()}.html").read_text()


def test_scrape_createfilea_offline(monkeypatch):
    html = load_fixture("createfilea")

    def fake_get(self, url, **kwargs):
        return html

    monkeypatch.setattr(HTTPClient, "get", fake_get)
    scraper = Win32APIScraper(language="us", quiet=True)
    result = scraper.scrape_function("CreateFileA")
    assert result["name"].startswith("CreateFileA")
    assert result["parameters"]
    assert result["signature"]


def test_scrape_virtualalloca_fallback(monkeypatch):
    html = load_fixture("virtualalloc")

    def fake_get(self, url, **kwargs):
        return html

    monkeypatch.setattr(HTTPClient, "get", fake_get)
    scraper = Win32APIScraper(language="us", quiet=True)
    result = scraper.scrape_function("VirtualAllocA")
    assert result["name"].startswith("VirtualAlloc")

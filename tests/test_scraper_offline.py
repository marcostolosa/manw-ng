import pathlib
import requests_mock
from manw_ng.core.scraper import Win32APIScraper
from manw_ng.utils.complete_win32_api_mapping import get_function_url

FIXTURE_DIR = pathlib.Path(__file__).with_name("fixtures")


def load_fixture(name: str) -> str:
    return (FIXTURE_DIR / f"{name.lower()}.html").read_text()


def test_scrape_createfilea_offline():
    html = load_fixture("createfilea")
    url = get_function_url("createfilea")
    with requests_mock.Mocker() as m:
        m.get(url, text=html)
        scraper = Win32APIScraper(language="us", quiet=True)
        result = scraper.scrape_function("CreateFileA")
    assert result["name"].startswith("CreateFileA")
    assert result["parameters"]
    assert result["signature"]

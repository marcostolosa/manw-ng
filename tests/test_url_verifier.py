import requests_mock

from manw_ng.utils.url_verifier import URLVerifier


def test_url_verifier_uses_cache():
    url = "https://example.com/test"
    with requests_mock.Mocker() as m:
        m.head(url, status_code=200)
        verifier = URLVerifier()
        assert verifier.verify_url(url) is True
        # Second call should hit cache and not perform another request
        m.head(url, status_code=404)
        assert verifier.verify_url(url) is True


def test_url_verifier_handles_failure():
    url = "https://example.com/fail"
    with requests_mock.Mocker() as m:
        m.head(url, status_code=500)
        verifier = URLVerifier()
        assert verifier.verify_url(url) is False

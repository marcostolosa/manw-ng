from unittest import mock

from manw_ng.utils.url_verifier import URLVerifier


def test_url_verifier_uses_cache():
    url = "https://example.com/test"
    with mock.patch("requests.Session.head") as mock_head:
        mock_head.return_value.status_code = 200
        verifier = URLVerifier()
        assert verifier.verify_url(url) is True
        # Second call should hit cache and not perform another request
        mock_head.return_value.status_code = 404
        assert verifier.verify_url(url) is True
        assert mock_head.call_count == 1


def test_url_verifier_handles_failure():
    url = "https://example.com/fail"
    with mock.patch("requests.Session.head") as mock_head:
        mock_head.return_value.status_code = 500
        verifier = URLVerifier()
        assert verifier.verify_url(url) is False
        assert mock_head.call_count == 1

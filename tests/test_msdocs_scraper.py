import pytest

from manw_ng.utils.msdocs_scraper import _swap_locale, classify_url


def test_swap_locale():
    base = "https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew"
    br = _swap_locale(base, "pt-br")
    assert "/pt-br/" in br
    assert br.endswith("nf-fileapi-createfilew")


def test_classify_url_sdk_function():
    url = "https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew"
    typ, header, area = classify_url(url)
    assert typ == "function"
    assert header == "fileapi"
    assert area == "SDK"


def test_classify_url_ddi_struct():
    url = "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_io_status_block"
    typ, header, area = classify_url(url)
    assert typ == "struct"
    assert header == "ntifs"
    assert area == "DDI"

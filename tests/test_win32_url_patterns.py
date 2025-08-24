from manw_ng.utils.win32_url_patterns import Win32URLPatterns


def test_getcommandline_mapping():
    url = Win32URLPatterns.generate_url("GetCommandLineA")
    assert url.endswith("/windows/win32/api/processenv/nf-processenv-getcommandlinea")
    assert Win32URLPatterns.guess_module("GetCommandLine") == "processenv"

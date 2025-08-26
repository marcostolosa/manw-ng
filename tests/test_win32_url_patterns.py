from manw_ng.utils.smart_url_generator import SmartURLGenerator
from manw_ng.utils.dll_map import detect_dll


def test_smart_url_generator_initialization():
    """Test SmartURLGenerator can be initialized"""
    generator = SmartURLGenerator()
    assert generator.function_patterns is not None
    assert len(generator.function_patterns) > 0


def test_dll_detection():
    """Test DLL detection functionality"""
    # Test some known function -> DLL mappings
    assert detect_dll("CreateProcess") == "kernel32.dll"
    assert detect_dll("OpenProcess") == "kernel32.dll"
    assert detect_dll("RegOpenKey") == "advapi32.dll"
    assert detect_dll("FindWindow") == "user32.dll"

    # Test case insensitive
    assert detect_dll("createprocess") == "kernel32.dll"
    assert detect_dll("CREATEPROCESS") == "kernel32.dll"


def test_dll_detection_priority():
    """Test that longer matches have priority"""
    # createprocessasuser should match advapi32.dll (more specific)
    # not kernel32.dll (less specific 'createprocess' match)
    result = detect_dll("CreateProcessAsUser")
    assert result == "advapi32.dll"

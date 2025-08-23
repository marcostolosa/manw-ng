import argparse
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "manw_ng_cli", Path(__file__).resolve().parent.parent / "manw-ng.py"
)
_manw_ng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_manw_ng)

validate = _manw_ng.validate_function_name


@pytest.mark.parametrize("name", ["CreateProcess", "VirtualAlloc123", "Open_File"])
def test_valid_names(name):
    assert validate(name) == name


@pytest.mark.parametrize("name", ["CreateProcess!", "Open-Process", "Invalid Name", ""])
def test_invalid_names(name):
    with pytest.raises(argparse.ArgumentTypeError):
        validate(name)

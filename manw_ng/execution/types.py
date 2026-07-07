"""Argument and return-type parsing for the WinAPI execution engine.

Supported CLI argument syntax (see the README "Execution Mode" section):
    123          unsigned int (32-bit, or 64-bit if it doesn't fit in 32)
    -5           signed int (same width rule)
    0x1000       hex, same width rule as decimal
    "text"       Unicode string (LPCWSTR)
    text         Unicode string, no quotes needed (LPCWSTR)
    $s:text      ANSI string (LPCSTR)
    $b:size      zeroed, writable buffer of `size` bytes (hexdumped after the call)
"""

from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from typing import Any, Optional

# Guard against accidental/malicious multi-gigabyte allocations from a typo'd size.
MAX_BUFFER_SIZE = 64 * 1024 * 1024  # 64 MiB

RETURN_TYPES = {
    "void": None,
    "u32": ctypes.c_uint32,
    "i32": ctypes.c_int32,
    "u64": ctypes.c_uint64,
    "i64": ctypes.c_int64,
    "bool": ctypes.c_bool,
    "ptr": ctypes.c_void_p,
}


class ArgumentError(ValueError):
    """Raised when a raw exec-mode argument can't be parsed."""


@dataclass
class ParsedArg:
    """A single parsed exec-mode argument, ready to pass to ctypes."""

    raw: str
    kind: str  # "int", "wstr", "str", "buffer"
    value: Any  # the ctypes-ready value passed as the actual call argument
    ctype: Any  # the ctypes type to use in argtypes
    buffer: Optional[ctypes.Array] = None  # populated for "buffer" kind, for hexdump


def parse_argument(raw: str) -> ParsedArg:
    """Parse a single raw CLI token into a typed, ctypes-ready argument."""
    if raw.startswith("$b:"):
        return _parse_buffer(raw)
    if raw.startswith("$s:"):
        return _parse_ansi_string(raw)

    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return ParsedArg(raw=raw, kind="wstr", value=raw[1:-1], ctype=ctypes.c_wchar_p)

    try:
        value = int(raw, 0)  # handles decimal and 0x-prefixed hex, including negatives
    except ValueError:
        return ParsedArg(raw=raw, kind="wstr", value=raw, ctype=ctypes.c_wchar_p)

    if -(2**31) <= value < 2**31:
        ctype = ctypes.c_int32 if value < 0 else ctypes.c_uint32
    else:
        ctype = ctypes.c_int64 if value < 0 else ctypes.c_uint64
    return ParsedArg(raw=raw, kind="int", value=ctype(value), ctype=ctype)


def _parse_ansi_string(raw: str) -> ParsedArg:
    text = raw[3:]
    encoding = "mbcs" if sys.platform == "win32" else "latin-1"
    encoded = text.encode(encoding, errors="replace")
    buf = ctypes.create_string_buffer(encoded)
    return ParsedArg(raw=raw, kind="str", value=buf, ctype=ctypes.c_char_p)


def _parse_buffer(raw: str) -> ParsedArg:
    size_text = raw[3:]
    try:
        size = int(size_text, 0)
    except ValueError as exc:
        raise ArgumentError(f"invalid buffer size in {raw!r}") from exc
    if size <= 0:
        raise ArgumentError(f"buffer size must be positive in {raw!r}")
    if size > MAX_BUFFER_SIZE:
        raise ArgumentError(
            f"buffer size {size} exceeds max allowed {MAX_BUFFER_SIZE} bytes in {raw!r}"
        )
    buf = ctypes.create_string_buffer(size)
    return ParsedArg(
        raw=raw, kind="buffer", value=buf, ctype=ctypes.c_void_p, buffer=buf
    )

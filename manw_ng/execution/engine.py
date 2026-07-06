"""WinAPI execution engine: resolves dll/function, builds a ctypes call, and runs it.

`ctypes.WinDLL` only exists/works on Windows. `ExecutionEngine._load_dll` is the single
seam that touches it, so tests can monkeypatch it with a fake DLL loader and exercise
every other piece of logic (dll/function resolution, argument parsing, return-type
handling, buffer hexdump, GetLastError reporting) on any platform.
"""

from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass
from typing import Any, List, Optional

from .memory import BufferTracker
from .types import RETURN_TYPES, ParsedArg, parse_argument

# winapiexec-style module abbreviations, kept from the original exec-mode stub.
DLL_ABBREVIATIONS = {
    "k": "kernel32.dll",
    "u": "user32.dll",
    "n": "ntdll.dll",
    "a32": "advapi32.dll",
    "g": "gdi32.dll",
    "ws2": "ws2_32.dll",
    "sh": "shell32.dll",
}


class ExecutionError(RuntimeError):
    """User-facing execution failure (bad dll/function/args/return type)."""


@dataclass
class CallResult:
    dll: str
    function: str
    return_value: Any
    elapsed_seconds: float
    buffer_dump: Optional[str] = None
    last_error_code: Optional[int] = None
    last_error_message: Optional[str] = None


class ExecutionEngine:
    """Resolves and invokes a single Windows API call from CLI-style arguments."""

    def __init__(self) -> None:
        # Seam for tests: monkeypatch this to avoid touching real DLLs.
        # `ctypes.WinDLL` doesn't exist at all on non-Windows platforms, so this
        # falls back to None there; tests overwrite it with a fake loader before
        # calling `call()`, and real CLI usage only ever runs on Windows anyway.
        self._load_dll = getattr(ctypes, "WinDLL", None)

    def resolve_dll(self, dll_spec: str) -> str:
        return DLL_ABBREVIATIONS.get(
            dll_spec.lower(), dll_spec if "." in dll_spec else f"{dll_spec}.dll"
        )

    def resolve_function(self, dll: Any, name: str, wide: bool):
        """Try `name`, then the W/A variants (or only W, if --wide was passed)."""
        candidates = [name + "W"] if wide else [name, name + "W", name + "A"]
        for candidate in candidates:
            try:
                return getattr(dll, candidate), candidate
            except AttributeError:
                continue
        raise ExecutionError(
            f"function '{name}' not found (tried: {', '.join(candidates)})"
        )

    def call(
        self,
        dll_spec: str,
        func_spec: str,
        raw_args: List[str],
        ret_type: str = "u32",
        wide: bool = False,
        show_error: bool = False,
    ) -> CallResult:
        if ret_type not in RETURN_TYPES:
            raise ExecutionError(
                f"unknown return type '{ret_type}' (choices: {', '.join(RETURN_TYPES)})"
            )

        if self._load_dll is None:
            raise ExecutionError(
                "WinDLL loading is only available on Windows (ctypes.WinDLL not found)"
            )

        resolved_dll = self.resolve_dll(dll_spec)
        try:
            dll = self._load_dll(resolved_dll, use_last_error=True)
        except OSError as exc:
            raise ExecutionError(f"could not load {resolved_dll}: {exc}") from exc

        func, resolved_name = self.resolve_function(dll, func_spec, wide)

        parsed: List[ParsedArg] = [parse_argument(raw) for raw in raw_args]
        tracker = BufferTracker()
        for index, arg in enumerate(parsed):
            tracker.track(index, arg)

        func.argtypes = [arg.ctype for arg in parsed]
        func.restype = RETURN_TYPES[ret_type]

        call_args = [arg.value for arg in parsed]

        start = time.perf_counter()
        return_value = func(*call_args)
        elapsed = time.perf_counter() - start

        result = CallResult(
            dll=resolved_dll,
            function=resolved_name,
            return_value=return_value,
            elapsed_seconds=elapsed,
            buffer_dump=tracker.render() if tracker.buffers else None,
        )

        if show_error:
            code = ctypes.get_last_error()
            result.last_error_code = code
            result.last_error_message = (
                ctypes.FormatError(code).strip()
                if code
                else "The operation completed successfully."
            )

        return result

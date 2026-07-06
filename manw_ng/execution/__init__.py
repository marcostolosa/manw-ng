"""WinAPI execution engine for MANW-NG's `exec` CLI mode."""

from .engine import ExecutionEngine, ExecutionError, CallResult
from .types import parse_argument, ArgumentError, RETURN_TYPES
from .memory import hexdump

__all__ = [
    "ExecutionEngine",
    "ExecutionError",
    "CallResult",
    "parse_argument",
    "ArgumentError",
    "RETURN_TYPES",
    "hexdump",
]

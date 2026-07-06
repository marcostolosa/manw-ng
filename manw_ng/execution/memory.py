"""Buffer tracking and hexdump helpers for the WinAPI execution engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .types import ParsedArg


def hexdump(data: bytes, width: int = 16) -> str:
    """Classic offset / hex / ASCII hexdump, matching common RE tool output."""
    if not data:
        return "(empty)"
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset : offset + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(width * 3 - 1)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset:08x}  {hex_part}  {ascii_part}")
    return "\n".join(lines)


@dataclass
class BufferTracker:
    """Tracks `$b:` buffer arguments allocated for a single exec-mode call."""

    buffers: List[Tuple[int, ParsedArg]] = field(default_factory=list)

    def track(self, index: int, arg: ParsedArg) -> None:
        if arg.kind == "buffer":
            self.buffers.append((index, arg))

    def render(self) -> str:
        sections = []
        for index, arg in self.buffers:
            raw_bytes = bytes(arg.buffer.raw)
            sections.append(
                f"Buffer #{index} ({len(raw_bytes)} bytes):\n{hexdump(raw_bytes)}"
            )
        return "\n\n".join(sections)

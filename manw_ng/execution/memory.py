"""
Elite Memory Management for Windows API Execution

Advanced memory management system with automatic cleanup,
leak prevention, and performance optimization.
"""

import ctypes as ct
from ctypes import wintypes as wt
import weakref
from typing import List, Dict, Any, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class ManagedBuffer:
    """Smart buffer with automatic cleanup"""

    def __init__(self, size: int, zero_init: bool = True):
        self.size = size
        self._buffer = (ct.c_ubyte * size)()
        if zero_init:
            ct.memset(self._buffer, 0, size)
        self._freed = False

    @property
    def address(self) -> int:
        """Get buffer address"""
        if self._freed:
            raise ValueError("Buffer has been freed")
        return ct.cast(self._buffer, ct.c_void_p).value

    @property
    def pointer(self) -> ct.c_void_p:
        """Get buffer as void pointer"""
        if self._freed:
            raise ValueError("Buffer has been freed")
        return ct.cast(self._buffer, ct.c_void_p)

    def read(self, offset: int = 0, length: Optional[int] = None) -> bytes:
        """Read data from buffer"""
        if self._freed:
            raise ValueError("Buffer has been freed")

        if length is None:
            length = self.size - offset

        if offset + length > self.size:
            raise ValueError("Read beyond buffer bounds")

        return ct.string_at(ct.addressof(self._buffer) + offset, length)

    def write(self, data: bytes, offset: int = 0):
        """Write data to buffer"""
        if self._freed:
            raise ValueError("Buffer has been freed")

        if offset + len(data) > self.size:
            raise ValueError("Write beyond buffer bounds")

        ct.memmove(ct.addressof(self._buffer) + offset, data, len(data))

    def hexdump(self, offset: int = 0, length: Optional[int] = None) -> str:
        """Generate hexdump of buffer contents"""
        data = self.read(offset, length)
        lines = []

        for i in range(0, len(data), 16):
            chunk = data[i : i + 16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            lines.append(f"{offset + i:08x}: {hex_part:<48} |{ascii_part}|")

        return "\n".join(lines)

    def free(self):
        """Explicitly free the buffer"""
        self._freed = True
        self._buffer = None

    def __del__(self):
        """Cleanup on garbage collection"""
        if not self._freed:
            self.free()


class StringManager:
    """Advanced string management for ASCII/Unicode conversion"""

    def __init__(self):
        self._strings: List[Any] = []

    def create_ascii_string(self, text: str) -> ct.c_char_p:
        """Create managed ASCII string"""
        encoded = text.encode("mbcs", errors="replace")
        string_obj = ct.c_char_p(encoded)
        self._strings.append(string_obj)
        return string_obj

    def create_unicode_string(self, text: str) -> wt.LPCWSTR:
        """Create managed Unicode string"""
        string_obj = wt.LPCWSTR(text)
        self._strings.append(string_obj)
        return string_obj

    def cleanup(self):
        """Clean up all managed strings"""
        self._strings.clear()


class MemoryManager:
    """Elite memory manager with leak prevention and performance optimization"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._buffers: Dict[int, ManagedBuffer] = {}
        self._string_manager = StringManager()
        self._cleanup_callbacks: List[callable] = []
        self._lock = threading.RLock()
        self._initialized = True

        logger.debug("MemoryManager initialized")

    def allocate_buffer(self, size: int, zero_init: bool = True) -> ManagedBuffer:
        """Allocate managed buffer with automatic tracking"""
        buffer = ManagedBuffer(size, zero_init)

        with self._lock:
            self._buffers[buffer.address] = buffer

        # Register cleanup callback
        def cleanup_callback():
            self._remove_buffer(buffer.address)

        weakref.finalize(buffer, cleanup_callback)

        logger.debug(f"Allocated buffer: {size} bytes at 0x{buffer.address:x}")
        return buffer

    def _remove_buffer(self, address: int):
        """Remove buffer from tracking"""
        with self._lock:
            if address in self._buffers:
                del self._buffers[address]
                logger.debug(f"Removed buffer at 0x{address:x}")

    def create_string(self, text: str, unicode: bool = False) -> Any:
        """Create managed string (ASCII or Unicode)"""
        if unicode:
            return self._string_manager.create_unicode_string(text)
        else:
            return self._string_manager.create_ascii_string(text)

    def register_cleanup(self, callback: callable):
        """Register cleanup callback"""
        with self._lock:
            self._cleanup_callbacks.append(callback)

    def cleanup_all(self):
        """Clean up all managed resources"""
        with self._lock:
            # Free all buffers
            for buffer in list(self._buffers.values()):
                try:
                    buffer.free()
                except Exception as e:
                    logger.error(f"Error freeing buffer: {e}")

            self._buffers.clear()

            # Clean up strings
            self._string_manager.cleanup()

            # Execute cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")

            self._cleanup_callbacks.clear()

            logger.debug("All managed resources cleaned up")

    def get_stats(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        with self._lock:
            total_size = sum(
                buf.size for buf in self._buffers.values() if not buf._freed
            )
            return {
                "active_buffers": len(self._buffers),
                "total_allocated": total_size,
                "cleanup_callbacks": len(self._cleanup_callbacks),
            }

    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.cleanup_all()
        except Exception:
            pass  # Ignore errors during cleanup


# Global memory manager instance
memory_manager = MemoryManager()

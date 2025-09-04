"""
MANW-NG Execution Module

Advanced Windows API execution engine inspired by winapiexec.
Provides elite-level runtime function invocation with intelligent 
parameter parsing and comprehensive error handling.
"""

from .engine import WinAPIExecutor
from .types import ArgumentParser, TypeConverter
from .memory import MemoryManager

__all__ = ['WinAPIExecutor', 'ArgumentParser', 'TypeConverter', 'MemoryManager']
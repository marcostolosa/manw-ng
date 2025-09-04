"""
Advanced Type System for Windows API Execution

Elite-level type conversion and parameter parsing inspired by winapiexec
with enhanced Python integration and safety features.
"""

import ctypes as ct
from ctypes import wintypes as wt
import re
import binascii
from typing import Any, Dict, List, Tuple, Union, Optional
from enum import Enum


class ArgumentType(Enum):
    """Supported argument types for Windows API calls"""

    ASCII_STRING = "s"  # $s: - ASCII string
    UNICODE_STRING = "u"  # $u: - Unicode string
    BUFFER = "b"  # $b: - Buffer allocation
    REFERENCE = "$"  # $$: - Reference to another argument
    ARRAY = "a"  # $a: - Array handling
    INTEGER = "i"  # Integer values
    POINTER = "p"  # Raw pointer
    HANDLE = "h"  # Windows handle
    BOOLEAN = "bool"  # Boolean value


class TypeConverter:
    """Elite type conversion system with enhanced safety"""

    # Enhanced type mapping with 64-bit safety
    TYPE_MAP = {
        "i8": (ct.c_int8, int),
        "u8": (ct.c_uint8, int),
        "i16": (ct.c_int16, int),
        "u16": (ct.c_uint16, int),
        "i32": (ct.c_int32, int),
        "u32": (ct.c_uint32, int),
        "i64": (ct.c_int64, int),
        "u64": (ct.c_uint64, int),
        "ptr": (ct.c_void_p, int),
        "bool": (wt.BOOL, bool),
        "handle": (wt.HANDLE, int),
        "hwnd": (wt.HWND, int),
        "hmodule": (wt.HMODULE, int),
        "lpvoid": (wt.LPVOID, int),
        "dword": (wt.DWORD, int),
        "word": (wt.WORD, int),
        "byte": (wt.BYTE, int),
    }

    # Module abbreviations (winapiexec compatibility)
    MODULE_ALIASES = {
        "k": "kernel32.dll",
        "k32": "kernel32.dll",
        "u": "user32.dll",
        "u32": "user32.dll",
        "a": "advapi32.dll",
        "a32": "advapi32.dll",
        "n": "ntdll.dll",
        "s": "shell32.dll",
        "s32": "shell32.dll",
        "ole": "ole32.dll",
        "oleaut": "oleaut32.dll",
        "ws2": "ws2_32.dll",
        "wininet": "wininet.dll",
        "crypt": "crypt32.dll",
        "version": "version.dll",
        "psapi": "psapi.dll",
        "dbghelp": "dbghelp.dll",
    }

    @classmethod
    def resolve_module(cls, module: str) -> str:
        """Resolve module abbreviations to full DLL names"""
        if "." not in module:
            return cls.MODULE_ALIASES.get(module.lower(), f"{module}.dll")
        return module

    @classmethod
    def parse_type_annotation(cls, annotation: str) -> Tuple[Any, Any]:
        """Parse type annotation into ctypes type and Python converter"""
        clean_ann = annotation.lower().strip()
        if clean_ann in cls.TYPE_MAP:
            return cls.TYPE_MAP[clean_ann]

        # Default to pointer for unknown types
        return ct.c_void_p, int


class ArgumentParser:
    """Elite argument parser inspired by winapiexec with enhanced features"""

    def __init__(self):
        self.converter = TypeConverter()
        self.allocated_buffers: List[Any] = []

    def parse_argument(self, arg: str) -> Tuple[Any, ArgumentType]:
        """
        Parse a single argument with winapiexec-style syntax

        Supported formats:
        - $s:text - ASCII string
        - $u:text - Unicode string
        - $b:size - Buffer allocation
        - $$:index - Reference to another argument
        - $a:type:count:values - Array
        - type:value - Typed value (i32:123, ptr:0x1000, etc.)
        - Raw numbers - Treated as u64
        """

        if not arg:
            raise ValueError("Empty argument")

        # Handle special prefixes ($s:, $u:, $b:, etc.)
        if arg.startswith("$"):
            return self._parse_special_argument(arg)

        # Handle quoted strings - auto-detect Unicode
        if (arg.startswith('"') and arg.endswith('"')) or (
            arg.startswith("'") and arg.endswith("'")
        ):
            text = arg[1:-1]  # Remove quotes
            return wt.LPCWSTR(text), ArgumentType.UNICODE_STRING

        # Handle typed arguments (type:value)
        if ":" in arg:
            return self._parse_typed_argument(arg)

        # Handle raw numbers - auto-detect best type
        try:
            value = int(arg, 0)  # Auto-detect base (0x for hex, 0 for octal)

            # Smart type detection based on value range
            if 0 <= value <= 0xFFFFFFFF:  # 32-bit range
                return ct.c_uint32(value), ArgumentType.INTEGER
            else:  # 64-bit range
                return ct.c_uint64(value), ArgumentType.INTEGER

        except ValueError:
            # If not a number, treat as Unicode string
            return wt.LPCWSTR(arg), ArgumentType.UNICODE_STRING

    def _parse_special_argument(self, arg: str) -> Tuple[Any, ArgumentType]:
        """Parse special arguments with $ prefix"""
        if arg.startswith("$s:"):
            # ASCII string
            text = arg[3:]
            return ct.c_char_p(text.encode("mbcs")), ArgumentType.ASCII_STRING

        elif arg.startswith("$u:"):
            # Unicode string
            text = arg[3:]
            return wt.LPCWSTR(text), ArgumentType.UNICODE_STRING

        elif arg.startswith("$b:"):
            # Buffer allocation
            try:
                size = int(arg[3:], 0)
                buffer = (ct.c_ubyte * size)()
                self.allocated_buffers.append(buffer)
                return ct.cast(buffer, wt.LPVOID), ArgumentType.BUFFER
            except ValueError:
                raise ValueError(f"Invalid buffer size: {arg}")

        elif arg.startswith("$$:"):
            # Reference to another argument (TODO: implement in execution phase)
            ref_index = int(arg[3:])
            return ref_index, ArgumentType.REFERENCE

        elif arg.startswith("$a:"):
            # Array handling (TODO: implement full array parsing)
            return self._parse_array_argument(arg)

        else:
            raise ValueError(f"Unknown special argument: {arg}")

    def _parse_typed_argument(self, arg: str) -> Tuple[Any, ArgumentType]:
        """Parse typed arguments (type:value)"""
        try:
            if ":" not in arg:
                raise ValueError("No type separator found")

            type_name, value_str = arg.split(":", 1)
            ctype, converter = self.converter.parse_type_annotation(type_name)

            # Special handling for hex values
            if value_str.startswith("0x") or value_str.startswith("0X"):
                value = converter(int(value_str, 16))
            else:
                value = converter(value_str if converter == str else int(value_str, 0))

            return ctype(value), ArgumentType.INTEGER

        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot parse typed argument {arg}: {e}")

    def _parse_array_argument(self, arg: str) -> Tuple[Any, ArgumentType]:
        """Parse array arguments ($a:type:count:values)"""
        # TODO: Implement full array parsing
        # Format: $a:i32:3:10,20,30
        parts = arg[3:].split(":", 3)
        if len(parts) < 3:
            raise ValueError(f"Invalid array format: {arg}")

        type_name, count_str, values_str = parts[0], parts[1], parts[2]
        count = int(count_str)
        values = values_str.split(",")

        if len(values) != count:
            raise ValueError(
                f"Array count mismatch: expected {count}, got {len(values)}"
            )

        ctype, converter = self.converter.parse_type_annotation(type_name)
        array_type = ctype * count
        array = array_type()

        for i, val_str in enumerate(values):
            array[i] = ctype(
                converter(val_str if converter == str else int(val_str, 0))
            )

        return ct.cast(array, ct.POINTER(ctype)), ArgumentType.ARRAY

    def cleanup(self):
        """Clean up allocated resources"""
        self.allocated_buffers.clear()


class FunctionSignature:
    """Enhanced function signature with intelligent type inference"""

    def __init__(self, name: str, dll: str, args: List[str], return_type: str = "u64"):
        self.name = name
        self.dll = dll
        self.args = args
        self.return_type = return_type
        self.parser = ArgumentParser()

    def parse_arguments(self) -> Tuple[List[Any], List[Any]]:
        """Parse all arguments and return ctypes values and types"""
        values = []
        types = []

        for arg in self.args:
            value, arg_type = self.parser.parse_argument(arg)
            values.append(value)
            types.append(type(value))

        return values, types

    def get_return_type(self) -> Any:
        """Get ctypes return type"""
        ctype, _ = TypeConverter.parse_type_annotation(self.return_type)
        return ctype

    def cleanup(self):
        """Clean up resources"""
        self.parser.cleanup()

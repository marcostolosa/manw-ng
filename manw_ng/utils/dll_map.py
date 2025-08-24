"""Mappings of keywords to their likely DLL names."""

from typing import Optional

DLL_MAP = {
    # Native API functions (ntdll.dll)
    "nt": "ntdll.dll",
    "zw": "ntdll.dll",
    "rtl": "ntdll.dll",
    "allocatevirtualmemory": "ntdll.dll",
    "freevirtualmemory": "ntdll.dll",
    # Kernel32 functions
    "createfile": "kernel32.dll",
    "readfile": "kernel32.dll",
    "writefile": "kernel32.dll",
    "getlogicaldrives": "kernel32.dll",
    "virtualalloc": "kernel32.dll",
    "loadlibrary": "kernel32.dll",
    "timezone": "kernel32.dll",
    "dynamic": "kernel32.dll",
    "time": "kernel32.dll",
    # Graphics/GDI
    "textout": "gdi32.dll",
    "bitblt": "gdi32.dll",
    "stretchblt": "gdi32.dll",
    "drawtext": "gdi32.dll",
    "getstockobject": "gdi32.dll",
    "deletedc": "gdi32.dll",
    "createbrush": "gdi32.dll",
    # UI Controls
    "toolbar": "comctl32.dll",
    "listview": "comctl32.dll",
    "treeview": "comctl32.dll",
    "createwindow": "user32.dll",
    # Registry and security
    "regopen": "advapi32.dll",
    "regquery": "advapi32.dll",
    "regset": "advapi32.dll",
    "geteffectiverights": "advapi32.dll",
    "cryptacquire": "advapi32.dll",
    # Shell and networking
    "shellexecute": "shell32.dll",
    "shgetfolder": "shell32.dll",
    "socket": "ws2_32.dll",
    "connect": "ws2_32.dll",
    "wsastartup": "ws2_32.dll",
    "internetopen": "wininet.dll",
    "httpopen": "wininet.dll",
    "messagebox": "user32.dll",
    "showwindow": "user32.dll",
    "getdc": "user32.dll",
    "certopen": "crypt32.dll",
    "certfind": "crypt32.dll",
}


def detect_dll(function_name: str) -> Optional[str]:
    """Return the DLL name based on simple keyword matching."""
    func_lower = function_name.lower()
    for key, dll in DLL_MAP.items():
        if key in func_lower:
            return dll
    return None

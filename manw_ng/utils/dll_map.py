"""Mappings of keywords to their likely DLL names."""

from typing import Optional

DLL_MAP = {
    # Native API functions (ntdll.dll)
    "nt": "ntdll.dll",
    "zw": "ntdll.dll",
    "rtl": "ntdll.dll",
    "allocatevirtualmemory": "ntdll.dll",
    "freevirtualmemory": "ntdll.dll",
    # KERNEL32.DLL - PROCESS & THREAD MANAGEMENT
    "createprocess": "kernel32.dll",  # CreateProcess, CreateProcessAsUser, etc.
    "openprocess": "kernel32.dll",
    "terminateprocess": "kernel32.dll",
    "getprocessid": "kernel32.dll",
    "getthreadid": "kernel32.dll",
    "createthread": "kernel32.dll",
    "createremotethread": "kernel32.dll",
    "openthread": "kernel32.dll",
    "suspendthread": "kernel32.dll",
    "resumethread": "kernel32.dll",
    "waitforsingleobject": "kernel32.dll",
    "waitformultipleobjects": "kernel32.dll",
    # KERNEL32.DLL - MEMORY MANAGEMENT
    "virtualalloc": "kernel32.dll",
    "virtualallocex": "kernel32.dll",
    "virtualfree": "kernel32.dll",
    "virtualfreeex": "kernel32.dll",
    "virtualprotect": "kernel32.dll",
    "virtualprotectex": "kernel32.dll",
    "virtualquery": "kernel32.dll",
    "virtualqueryex": "kernel32.dll",
    "readprocessmemory": "kernel32.dll",
    "writeprocessmemory": "kernel32.dll",
    "heapcreate": "kernel32.dll",
    "heapalloc": "kernel32.dll",
    "heapfree": "kernel32.dll",
    "globalalloc": "kernel32.dll",
    "globalfree": "kernel32.dll",
    "localalloc": "kernel32.dll",
    "localfree": "kernel32.dll",
    # KERNEL32.DLL - FILE OPERATIONS
    "createfile": "kernel32.dll",
    "readfile": "kernel32.dll",
    "writefile": "kernel32.dll",
    "deletefile": "kernel32.dll",
    "copyfile": "kernel32.dll",
    "movefile": "kernel32.dll",
    "findfirstfile": "kernel32.dll",
    "findnextfile": "kernel32.dll",
    "findclose": "kernel32.dll",
    "getfileattributes": "kernel32.dll",
    "setfileattributes": "kernel32.dll",
    "getfiletime": "kernel32.dll",
    "setfiletime": "kernel32.dll",
    "getlogicaldrives": "kernel32.dll",
    # KERNEL32.DLL - LIBRARY LOADING
    "loadlibrary": "kernel32.dll",
    "freelibrary": "kernel32.dll",
    "getprocaddress": "kernel32.dll",
    "getmodulehandle": "kernel32.dll",
    "getmodulefilename": "kernel32.dll",
    # KERNEL32.DLL - OTHER
    "timezone": "kernel32.dll",
    "dynamic": "kernel32.dll",
    "time": "kernel32.dll",
    "getlasterror": "kernel32.dll",
    "setlasterror": "kernel32.dll",
    "formatmessage": "kernel32.dll",
    "sleep": "kernel32.dll",
    "getcommandline": "kernel32.dll",
    "getcomputername": "kernel32.dll",
    "getenvironmentvariable": "kernel32.dll",
    "setenvironmentvariable": "kernel32.dll",
    # ADVAPI32.DLL - SECURITY & TOKENS
    "adjusttokenprivileges": "advapi32.dll",
    "duplicatetoken": "advapi32.dll",
    "openprocesstoken": "advapi32.dll",
    "openthreadtoken": "advapi32.dll",
    "lookupprivilegevalue": "advapi32.dll",
    "impersonateloggedonuser": "advapi32.dll",
    "reverttoself": "advapi32.dll",
    "logonuser": "advapi32.dll",
    "createprocessasuser": "advapi32.dll",  # IMPORTANT!
    "createprocesswithlogon": "advapi32.dll",
    "createprocesswithtoken": "advapi32.dll",
    # ADVAPI32.DLL - REGISTRY
    "regopen": "advapi32.dll",
    "regcreate": "advapi32.dll",
    "regquery": "advapi32.dll",
    "regset": "advapi32.dll",
    "regdelete": "advapi32.dll",
    "regenum": "advapi32.dll",
    "regclose": "advapi32.dll",
    # ADVAPI32.DLL - SERVICES
    "openscmanager": "advapi32.dll",
    "openservice": "advapi32.dll",
    "createservice": "advapi32.dll",
    "deleteservice": "advapi32.dll",
    "startservice": "advapi32.dll",
    "controlservice": "advapi32.dll",
    "queryservicestatus": "advapi32.dll",
    "enumservices": "advapi32.dll",
    # ADVAPI32.DLL - CRYPTOGRAPHY
    "cryptacquire": "advapi32.dll",
    "cryptrelease": "advapi32.dll",
    "cryptcreate": "advapi32.dll",
    "cryptdecrypt": "advapi32.dll",
    "cryptencrypt": "advapi32.dll",
    "cryptgenkey": "advapi32.dll",
    "crypthash": "advapi32.dll",
    # ADVAPI32.DLL - ACL & SECURITY
    "geteffectiverights": "advapi32.dll",
    "seteffectiverights": "advapi32.dll",
    "getacl": "advapi32.dll",
    "setacl": "advapi32.dll",
    "getsecurityinfo": "advapi32.dll",
    "setsecurityinfo": "advapi32.dll",
    # USER32.DLL - WINDOW MANAGEMENT
    "findwindow": "user32.dll",
    "findwindowex": "user32.dll",
    "getwindowtext": "user32.dll",
    "setwindowtext": "user32.dll",
    "showwindow": "user32.dll",
    "createwindow": "user32.dll",
    "destroywindow": "user32.dll",
    "getwindowrect": "user32.dll",
    "setwindowpos": "user32.dll",
    "enumwindows": "user32.dll",
    "enumchildwindows": "user32.dll",
    # USER32.DLL - MESSAGING
    "sendmessage": "user32.dll",
    "postmessage": "user32.dll",
    "getmessage": "user32.dll",
    "peekmessage": "user32.dll",
    "dispatchmessage": "user32.dll",
    "messagebox": "user32.dll",
    # USER32.DLL - HOOKING
    "setwindowshook": "user32.dll",
    "unhookwindowshook": "user32.dll",
    "callnexthook": "user32.dll",
    # USER32.DLL - INPUT
    "getkeyboardstate": "user32.dll",
    "setkeyboardstate": "user32.dll",
    "getcursorpos": "user32.dll",
    "setcursorpos": "user32.dll",
    "mouse_event": "user32.dll",
    "keybd_event": "user32.dll",
    # USER32.DLL - OTHER
    "getdc": "user32.dll",
    "releasedc": "user32.dll",
    "getdesktopwindow": "user32.dll",
    "getforegroundwindow": "user32.dll",
    "setforegroundwindow": "user32.dll",
    # GDI32.DLL - Graphics/GDI
    "textout": "gdi32.dll",
    "bitblt": "gdi32.dll",
    "stretchblt": "gdi32.dll",
    "drawtext": "gdi32.dll",
    "getstockobject": "gdi32.dll",
    "deletedc": "gdi32.dll",
    "createdc": "gdi32.dll",
    "createcompatibledc": "gdi32.dll",
    "createbrush": "gdi32.dll",
    "createpen": "gdi32.dll",
    "createfont": "gdi32.dll",
    "selectobject": "gdi32.dll",
    "deleteobject": "gdi32.dll",
    # PSAPI.DLL - Process Information
    "enumprocesses": "psapi.dll",
    "enumprocessmodules": "psapi.dll",
    "getprocessimagefilename": "psapi.dll",
    "getprocessmemoryinfo": "psapi.dll",
    "getperformanceinfo": "psapi.dll",
    # WS2_32.DLL - Networking
    "wsastartup": "ws2_32.dll",
    "wsacleanup": "ws2_32.dll",
    "socket": "ws2_32.dll",
    "bind": "ws2_32.dll",
    "listen": "ws2_32.dll",
    "accept": "ws2_32.dll",
    "connect": "ws2_32.dll",
    "send": "ws2_32.dll",
    "recv": "ws2_32.dll",
    "closesocket": "ws2_32.dll",
    "gethostbyname": "ws2_32.dll",
    "inet_addr": "ws2_32.dll",
    # WININET.DLL - Internet
    "internetopen": "wininet.dll",
    "internetconnect": "wininet.dll",
    "httpopenrequest": "wininet.dll",
    "httpsendrequest": "wininet.dll",
    "httpqueryinfo": "wininet.dll",
    "internetreadfile": "wininet.dll",
    "internetclosehandle": "wininet.dll",
    "urldownloadtofile": "urlmon.dll",
    # SHELL32.DLL - Shell
    "shellexecute": "shell32.dll",
    "shgetfolder": "shell32.dll",
    "shgetspecialfolder": "shell32.dll",
    "shbrowseforfolder": "shell32.dll",
    "dragacceptfiles": "shell32.dll",
    "dragqueryfile": "shell32.dll",
    # CRYPT32.DLL - Certificates
    "certopen": "crypt32.dll",
    "certfind": "crypt32.dll",
    "certclose": "crypt32.dll",
    "certenum": "crypt32.dll",
    # COMCTL32.DLL - Common Controls
    "toolbar": "comctl32.dll",
    "listview": "comctl32.dll",
    "treeview": "comctl32.dll",
    "tabcontrol": "comctl32.dll",
    "progressbar": "comctl32.dll",
    "statusbar": "comctl32.dll",
    # NTDLL.DLL - Additional Native API
    "ntcreatefile": "ntdll.dll",
    "ntcreateprocess": "ntdll.dll",
    "ntqueryinformationprocess": "ntdll.dll",
    "ntqueryinformationthread": "ntdll.dll",
    "ntopenprocess": "ntdll.dll",
    "ntopenthread": "ntdll.dll",
    "ntterminateprocess": "ntdll.dll",
    "ntterminatethread": "ntdll.dll",
    "ntclose": "ntdll.dll",
    "ntreadfile": "ntdll.dll",
    "ntwritefile": "ntdll.dll",
    "ntdeviceiocontrolfile": "ntdll.dll",
}


def detect_dll(function_name: str) -> Optional[str]:
    """Return the DLL name based on intelligent keyword matching."""
    func_lower = function_name.lower()

    # Priority matching - longer matches first (more specific)
    matches = [(key, dll) for key, dll in DLL_MAP.items() if key in func_lower]
    if matches:
        # Sort by key length descending (longer = more specific)
        matches.sort(key=lambda x: len(x[0]), reverse=True)
        return matches[0][1]

    # Additional heuristics for common patterns
    if func_lower.startswith("create"):
        if (
            "processasuser" in func_lower
            or "processwithlogon" in func_lower
            or "processwithtoken" in func_lower
        ):
            return "advapi32.dll"  # Security-related process creation
        elif "process" in func_lower:
            return "kernel32.dll"  # Most process creation functions are in kernel32
        elif "file" in func_lower:
            return "kernel32.dll"
        elif "window" in func_lower:
            return "user32.dll"
        elif "service" in func_lower:
            return "advapi32.dll"
    elif func_lower.startswith("open"):
        if "process" in func_lower:
            return "kernel32.dll"
        elif "thread" in func_lower:
            return "kernel32.dll"
        elif "key" in func_lower:
            return "advapi32.dll"
        elif "service" in func_lower:
            return "advapi32.dll"
    elif func_lower.startswith(("get", "set")):
        if "window" in func_lower:
            return "user32.dll"
        elif "file" in func_lower:
            return "kernel32.dll"
        elif "process" in func_lower:
            return "kernel32.dll" if "psapi" not in func_lower else "psapi.dll"
    elif func_lower.startswith("enum"):
        if "process" in func_lower:
            return "psapi.dll"
        elif "window" in func_lower:
            return "user32.dll"
        elif "service" in func_lower:
            return "advapi32.dll"

    return None

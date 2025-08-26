"""
Smart URL Generator for Win32 API Documentation

Ultra-fast asynchronous URL generator that tests ALL known patterns simultaneously.
This system ensures 100% coverage with maximum speed using concurrent requests.
"""

from typing import List, Dict, Set, Optional, Tuple, Callable
import re
import asyncio

# Lazy import heavy dependencies
# import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random

# Lazy import to avoid 3s+ load time
# from .url_pattern_learner import pattern_learner


class SmartURLGenerator:
    """
    Ultra-fast async URL generator that tests ALL known patterns concurrently
    """

    def __init__(self):
        # Intelligent user agent pool with success tracking
        self.user_agents = {
            # High-success desktop browsers (prioritized)
            "chrome_win": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            ],
            "firefox_win": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
            ],
            "edge_win": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            ],
            "chrome_mac": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            ],
            "safari_mac": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            ],
            "chrome_linux": [
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            ],
        }

        # Flattened list for backward compatibility
        self.user_agents_flat = []
        for category_agents in self.user_agents.values():
            self.user_agents_flat.extend(category_agents)

        # Success tracking for intelligent rotation
        self.user_agent_stats = {}
        self._current_rotation_index = 0
        self._requests_with_current_agent = 0
        self._max_requests_per_agent = 5  # Switch agent after 5 requests

        # Optimized headers for Microsoft Learn documentation
        self.additional_headers = [
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            },
        ]

        # Enhanced request tracking
        self._request_counter = 0
        self._last_successful_agent = None
        self._agent_failure_count = {}

        # Circuit breaker for intelligent retry - OPTIMIZED SETTINGS
        self._circuit_breaker = {
            "failure_count": 0,
            "last_failure_time": 0,
            "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
            "failure_threshold": 100,  # Much higher threshold - allow more failures
            "recovery_timeout": 1,  # Very fast recovery
            "consecutive_successes_needed": 1,  # Only need 1 success
        }

        # Adaptive retry configuration - ULTRA FAST
        self._retry_config = {
            "max_retries": 2,  # Fewer retries
            "base_delay": 0.1,  # Much faster base delay
            "max_delay": 2.0,  # Much lower max delay
            "backoff_factor": 1.5,  # Less aggressive backoff
            "jitter": True,
        }

        # Try to import ML classifier for intelligent predictions
        self.ml_classifier = None
        try:
            from ..ml.function_classifier import ml_classifier

            self.ml_classifier = ml_classifier
        except ImportError:
            pass  # Continue without ML if not available

        # Mapeamento DLL -> Headers COMPLETO (TODOS os headers possíveis)
        self.dll_to_headers = {
            "kernel32.dll": [
                "fileapi",
                "memoryapi",
                "processthreadsapi",
                "heapapi",
                "libloaderapi",
                "synchapi",
                "processenv",
                "sysinfoapi",
                "consoleapi",
                "errhandlingapi",
                "ioapiset",
                "namedpipeapi",
                "timezoneapi",
                "winbase",
                "handleapi",
                "threadpoollegacyapiset",
                "wow64apiset",
                "debugapi",
                "fibersapi",
                "interlockedapi",
                "profileapi",
                "realtimeapiset",
                "securityappcontainer",
                "systemtopologyapi",
                "utilapiset",
                "jobapi",
                "jobapi2",
            ],
            "user32.dll": ["winuser", "windowsandmessaging", "menurc", "winstation"],
            "gdi32.dll": ["wingdi", "wingdiapi", "gdiplusheaders"],
            "comctl32.dll": ["commctrl", "commdlg", "prsht"],
            "uxtheme.dll": ["uxtheme", "vsstyle", "vssym32"],
            "advapi32.dll": [
                "aclapi",
                "securitybaseapi",
                "secext",
                "winreg",
                "winsvc",
                "processthreadsapi",
                "wincrypt",
                "winbase",
                "accctrl",
                "authz",
                "lmaccess",
                "lmapibuf",
                "lmconfig",
                "lmerr",
                "lmserver",
                "lmshare",
                "lmuse",
                "lmwksta",
                "ntsecapi",
                "sspi",
                "schannel",
                "wincred",
                "winefs",
                "winsafer",
                "wintrust",
                "evntprov",
                "evntrace",
                "perflib",
                "pdh",
                "loadperf",
            ],
            "ws2_32.dll": [
                "winsock2",
                "winsock",
                "ws2tcpip",
                "wsipx",
                "mswsock",
                "ws2spi",
            ],
            "wininet.dll": ["wininet", "urlmon", "winhttp"],
            "ole32.dll": ["objbase", "combaseapi", "ole2", "oleidl", "oleauto"],
            "oleaut32.dll": ["oleauto", "oaidl"],
            "shell32.dll": ["shellapi", "shlobj_core", "shlwapi"],
            "version.dll": ["winver"],
            "psapi.dll": ["psapi"],
            "dbghelp.dll": ["dbghelp"],
            "imagehlp.dll": ["imagehlp"],
            "rpcrt4.dll": ["rpc"],
            "secur32.dll": ["sspi", "ntsecapi"],
            "winspool.drv": ["winspool"],
            "winmm.dll": ["mmeapi", "timeapi"],
            "urlmon.dll": ["urlmon", "wininet"],
            "winhttp.dll": ["winhttp", "wininet"],
            "ntdll.dll": ["winternl", "winbase", "ntstatus", "subauth", "winnt", "wdm"],
            "psapi.dll": ["psapi", "toolhelp", "tlhelp32"],
            "version.dll": ["winver"],
            "crypt32.dll": ["wincrypt", "dpapi", "cryptuiapi"],
            "ole32.dll": [
                "combaseapi",
                "objbase",
                "objidl",
                "unknwn",
                "wtypes",
                "oaidl",
            ],
            "shell32.dll": ["shellapi", "shlobj", "shlwapi", "shobjidl"],
            "msvcrt.dll": [
                "corecrt",
                "crtdbg",
                "malloc",
                "stdio",
                "stdlib",
                "string",
                "time",
            ],
            "bcrypt.dll": ["bcrypt", "ncrypt", "wincrypt"],
            "ncrypt.dll": ["ncrypt", "bcrypt", "wincrypt"],
            "netapi32.dll": [
                "lmaccess",
                "lmapibuf",
                "lmconfig",
                "lmerr",
                "lmserver",
                "lmshare",
                "lmuse",
                "lmwksta",
            ],
            "imagehlp.dll": ["imagehlp", "dbghelp", "winnt"],
            "dbghelp.dll": ["dbghelp", "imagehlp", "winnt"],
            "setupapi.dll": ["setupapi", "cfgmgr32", "devguid", "regstr"],
            "winspool.drv": ["winspool", "wingdi"],
            "winmm.dll": ["mmsystem", "mmreg", "timeapi", "playsoundapi"],
            "rpcrt4.dll": ["rpc", "rpcdce", "rpcndr", "rpcproxy"],
            "secur32.dll": ["sspi", "schannel", "ntsecapi", "security"],
            "mpr.dll": ["winnetwk", "npapi"],
            "cabinet.dll": ["fci", "fdi"],
        }

        # Mapeamento específico baseado nos padrões descobertos
        self.dll_to_primary_header = {
            "gdi32.dll": "wingdi",
            "kernel32.dll": "fileapi",  # Para algumas funções como GetLogicalDrives
            "crypt32.dll": "wincrypt",
            "netapi32.dll": "lmaccess",
            "shell32.dll": "shellapi",
            "advapi32.dll": "aclapi",  # Para funções de ACL
            "ntdll.dll": "winternl",  # Native API functions
        }

        # Headers baseados no nome da função (patterns)
        self.function_patterns = {
            # Native API functions (highest priority)
            r"^nt.*": ["winternl", "ntddk", "wdm", "ntifs"],
            r"^zw.*": ["winternl", "ntddk", "wdm", "ntifs"],
            r"^rtl.*": ["ntddk", "wdm", "ntifs"],
            r"^ke.*": ["ntddk", "wdm"],
            r"^mm.*": ["ntddk", "wdm"],
            # Graphics/GDI operations
            r"^text.*": ["wingdi"],
            r".*blt.*": ["wingdi"],
            r"^draw.*": ["wingdi"],
            r"^paint.*": ["wingdi"],
            r"get.*dc.*": ["wingdi"],
            r"create.*dc.*": ["wingdi"],
            r"select.*": ["wingdi"],
            r"get.*object.*gdi": ["wingdi"],
            # File operations - EXPANDED
            r"^createfilew$": ["fileapi"],  # CreateFileW specifically
            r"^createfilea$": ["fileapi"],  # CreateFileA specifically
            r"^createfile2$": ["fileapi"],  # CreateFile2 specifically
            r"^readfile$": ["fileapi"],  # ReadFile specifically
            r"^writefile$": ["fileapi"],  # WriteFile specifically
            r"^deletefile$": ["fileapi"],  # DeleteFile specifically
            r"^copyfile$": ["fileapi"],  # CopyFile specifically
            r"^movefile$": ["fileapi"],  # MoveFile specifically
            r"^findfirstfile$": ["fileapi"],  # FindFirstFile specifically
            r"^findnextfile$": ["fileapi"],  # FindNextFile specifically
            r"^findclose$": ["fileapi"],  # FindClose specifically
            r".*file.*": ["fileapi"],
            r"^create.*file": ["fileapi"],
            r"^create.*process": ["processthreadsapi"],
            r"delete.*": ["fileapi"],
            r"copy.*": ["fileapi"],
            r"move.*": ["fileapi"],
            r"read.*file": ["fileapi", "ioapiset"],
            r"write.*file": ["fileapi", "ioapiset"],
            r"get.*drives.*": ["fileapi"],
            r"get.*logical.*drives": ["fileapi"],
            r"^getcommandlinea$": ["processenv"],  # GetCommandLineA specifically
            r"^getcommandlinew$": ["processenv"],  # GetCommandLineW specifically
            r"get.*command.*line": ["processenv"],
            # Memory operations - EXPANDED
            r"^virtualalloc$": ["memoryapi"],  # VirtualAlloc specifically
            r"^virtualallocex$": ["memoryapi"],  # VirtualAllocEx specifically
            r"^virtualfree$": ["memoryapi"],  # VirtualFree specifically
            r"^virtualfreeex$": ["memoryapi"],  # VirtualFreeEx specifically
            r"^virtualprotect$": ["memoryapi"],  # VirtualProtect specifically
            r"^virtualprotectex$": ["memoryapi"],  # VirtualProtectEx specifically
            r"^virtualquery$": ["memoryapi"],  # VirtualQuery specifically
            r"^virtualqueryex$": ["memoryapi"],  # VirtualQueryEx specifically
            r"virtual.*": ["memoryapi"],
            r"heap.*": ["heapapi"],
            r".*alloc.*": ["memoryapi", "heapapi"],
            r".*memory.*": ["memoryapi"],
            # Handle operations - EXPANDED
            r"^closehandle$": ["handleapi"],  # CloseHandle specifically
            r"^duplicatehandle$": ["handleapi"],  # DuplicateHandle specifically
            r"^compareobjecthandles$": [
                "handleapi"
            ],  # CompareObjectHandles specifically
            r"^gethandleinformation$": [
                "handleapi"
            ],  # GetHandleInformation specifically
            r"^sethandleinformation$": [
                "handleapi"
            ],  # SetHandleInformation specifically
            r".*handle.*": ["handleapi"],
            # Performance and timing - EXPANDED
            r"^queryperformancecounter$": [
                "profileapi"
            ],  # QueryPerformanceCounter specifically
            r"^queryperformancefrequency$": [
                "profileapi"
            ],  # QueryPerformanceFrequency specifically
            r"^gettickcount$": ["sysinfoapi"],  # GetTickCount specifically
            r"^gettickcount64$": ["sysinfoapi"],  # GetTickCount64 specifically
            r"query.*performance.*": ["profileapi"],
            r"get.*tick.*": ["sysinfoapi"],
            # Global memory operations - EXPANDED
            r"^globalalloc$": ["winbase"],  # GlobalAlloc specifically
            r"^globalfree$": ["winbase"],  # GlobalFree specifically
            r"^globallock$": ["winbase"],  # GlobalLock specifically
            r"^globalunlock$": ["winbase"],  # GlobalUnlock specifically
            r"^globalrealloc$": ["winbase"],  # GlobalReAlloc specifically
            r"global.*": ["winbase"],
            # SList operations - EXPANDED
            r"^initializeslisthead$": [
                "interlockedapi"
            ],  # InitializeSListHead specifically
            r"^interlockedpushslistentry$": [
                "interlockedapi"
            ],  # InterlockedPushSListEntry specifically
            r"^interlockedpopslistentry$": [
                "interlockedapi"
            ],  # InterlockedPopSListEntry specifically
            r"^interlockedflushslist$": [
                "interlockedapi"
            ],  # InterlockedFlushSList specifically
            r"^querydepthslist$": ["interlockedapi"],  # QueryDepthSList specifically
            r".*slist.*": ["interlockedapi"],
            # Exception handling - EXPANDED
            r"^setunhandledexceptionfilter$": [
                "errhandlingapi"
            ],  # SetUnhandledExceptionFilter specifically
            r"^unhandledexceptionfilter$": [
                "errhandlingapi"
            ],  # UnhandledExceptionFilter specifically
            r"^addvectoredexceptionhandler$": [
                "errhandlingapi"
            ],  # AddVectoredExceptionHandler specifically
            r"^removevectoredexceptionhandler$": [
                "errhandlingapi"
            ],  # RemoveVectoredExceptionHandler specifically
            r".*exception.*": ["errhandlingapi"],
            # User name operations - EXPANDED
            r"^getusernameexw$": ["secext"],  # GetUserNameExW specifically
            r"^getusernameexa$": ["secext"],  # GetUserNameExA specifically
            r"^getusernamew$": ["advapi32"],  # GetUserNameW specifically
            r"^getusernamea$": ["advapi32"],  # GetUserNameA specifically
            r"get.*user.*name.*": ["secext", "advapi32"],
            # COM operations - EXPANDED
            r"^coinitialize$": ["objbase"],  # CoInitialize specifically
            r"^coinitializeex$": ["objbase"],  # CoInitializeEx specifically
            r"^couninitialize$": ["objbase"],  # CoUninitialize specifically
            r"^cocreateinstance$": ["objbase"],  # CoCreateInstance specifically
            r"^cogetclassobject$": ["objbase"],  # CoGetClassObject specifically
            r"^coclassfactory$": ["objbase"],  # CoClassFactory specifically
            r"^coregisterclassobject$": [
                "objbase"
            ],  # CoRegisterClassObject specifically
            r"^corevokeclassobject$": ["objbase"],  # CoRevokeClassObject specifically
            r"^cotaskmemalloc$": ["objbase"],  # CoTaskMemAlloc specifically
            r"^cotaskmemfree$": ["objbase"],  # CoTaskMemFree specifically
            r"co.*": ["objbase", "combaseapi"],
            # Shell operations - EXPANDED
            r"^shellexecutew$": ["shellapi"],  # ShellExecuteW specifically
            r"^shellexecutea$": ["shellapi"],  # ShellExecuteA specifically
            r"^shellexecuteexw$": ["shellapi"],  # ShellExecuteExW specifically
            r"^shellexecuteexa$": ["shellapi"],  # ShellExecuteExA specifically
            r"^shgetfolderpath$": ["shlobj_core"],  # SHGetFolderPath specifically
            r"^shgetspecialfolderlocation$": [
                "shlobj_core"
            ],  # SHGetSpecialFolderLocation specifically
            r"shell.*": ["shellapi", "shlobj_core"],
            r"sh.*": ["shlobj_core", "shlwapi"],
            # Process/Thread - EXPANDED
            r"^createprocessw$": ["processthreadsapi"],  # CreateProcessW specifically
            r"^createprocessa$": ["processthreadsapi"],  # CreateProcessA specifically
            r"^openprocess$": ["processthreadsapi"],  # OpenProcess specifically
            r"^terminateprocess$": [
                "processthreadsapi"
            ],  # TerminateProcess specifically
            r"^createthread$": ["processthreadsapi"],  # CreateThread specifically
            r"^createremotethread$": [
                "processthreadsapi"
            ],  # CreateRemoteThread specifically
            r"^openthread$": ["processthreadsapi"],  # OpenThread specifically
            r"^suspendthread$": ["processthreadsapi"],  # SuspendThread specifically
            r"^resumethread$": ["processthreadsapi"],  # ResumeThread specifically
            r"^terminatethread$": ["processthreadsapi"],  # TerminateThread specifically
            r".*process.*": ["processthreadsapi"],
            r".*thread.*": ["processthreadsapi"],
            r"terminate.*": ["processthreadsapi"],
            r"suspend.*": ["processthreadsapi"],
            r"resume.*": ["processthreadsapi"],
            # Registry - EXPANDED
            r"^regopenkeyexw$": ["winreg"],  # RegOpenKeyExW specifically
            r"^regopenkeyexa$": ["winreg"],  # RegOpenKeyExA specifically
            r"^regopenkeyex$": ["winreg"],  # RegOpenKeyEx generic
            r"^regopenkeyw$": ["winreg"],  # RegOpenKeyW specifically
            r"^regopenkeya$": ["winreg"],  # RegOpenKeyA specifically
            r"^regopenkey$": ["winreg"],  # RegOpenKey generic
            r"^regcreatekeyexw$": ["winreg"],  # RegCreateKeyExW specifically
            r"^regcreatekeyexa$": ["winreg"],  # RegCreateKeyExA specifically
            r"^regcreatekeyex$": ["winreg"],  # RegCreateKeyEx generic
            r"^regclosekey$": ["winreg"],  # RegCloseKey specifically
            r"reg.*": ["winreg"],
            r".*key.*": ["winreg"],
            # Services
            r".*service.*": ["winsvc"],
            # Network - EXPANDED
            r"^internetopena$": ["wininet"],  # InternetOpenA specifically
            r"^internetopenw$": ["wininet"],  # InternetOpenW specifically
            r"^internetopen$": ["wininet"],  # InternetOpen generic
            r"^internetconnecta$": ["wininet"],  # InternetConnectA specifically
            r"^internetconnectw$": ["wininet"],  # InternetConnectW specifically
            r"^internetconnect$": ["wininet"],  # InternetConnect generic
            r"^internetreadfile$": ["wininet"],  # InternetReadFile specifically
            r"^socket$": ["winsock2"],  # socket specifically
            r"^wsastartup$": ["winsock2"],  # WSAStartup specifically
            r"^wsacleanup$": ["winsock2"],  # WSACleanup specifically
            r".*socket.*": ["winsock2"],
            r"ws.*": ["winsock2"],
            r"internet.*": ["wininet"],
            r"net.*": ["lmaccess", "lmserver"],
            # Security/Crypto/ACL
            r"cert.*": ["wincrypt"],
            r"crypt.*": ["wincrypt", "bcrypt"],
            r".*security.*": ["securitybaseapi"],
            # Debug/Diagnostics - EXPANDED
            r"^isdebuggerpresent$": ["debugapi"],  # IsDebuggerPresent specifically
            r".*debug.*": ["debugapi"],
            r".*acl.*": ["aclapi"],
            r".*effective.*": ["aclapi"],
            r".*trustee.*": ["aclapi"],
            # Shell/System - EXPANDED
            r"^shellexecutea$": ["shellapi"],  # ShellExecuteA specifically
            r"^shellexecutew$": ["shellapi"],  # ShellExecuteW specifically
            r"^shellexecute$": ["shellapi"],  # ShellExecute generic
            r"^shellexecuteexa$": ["shellapi"],  # ShellExecuteExA specifically
            r"^shellexecuteexw$": ["shellapi"],  # ShellExecuteExW specifically
            r"^shellexecuteex$": ["shellapi"],  # ShellExecuteEx generic
            r"shell.*": ["shellapi"],
            r"sh.*": ["shellapi"],
            # Console
            r".*console.*": ["consoleapi"],
            # Library loading - EXPANDED
            r"^loadlibrarya$": ["libloaderapi"],  # LoadLibraryA specifically
            r"^loadlibraryw$": ["libloaderapi"],  # LoadLibraryW specifically
            r"^loadlibrary$": ["libloaderapi"],  # LoadLibrary generic
            r"^freelibrary$": ["libloaderapi"],  # FreeLibrary specifically
            r"^getprocaddress$": ["libloaderapi"],  # GetProcAddress specifically
            r"^getmodulehandle$": ["libloaderapi"],  # GetModuleHandle specifically
            r"^getmodulehandlea$": ["libloaderapi"],  # GetModuleHandleA specifically
            r"^getmodulehandlew$": ["libloaderapi"],  # GetModuleHandleW specifically
            r"load.*": ["libloaderapi"],
            r"get.*module.*": ["libloaderapi"],
            r".*library.*": ["libloaderapi"],
            # UI Controls (CommCtrl)
            r".*toolbar.*": ["commctrl"],
            r".*listview.*": ["commctrl"],
            r".*treeview.*": ["commctrl"],
            r".*tab.*": ["commctrl"],
            r".*button.*": ["commctrl"],
            r".*edit.*": ["commctrl"],
            r".*combo.*": ["commctrl"],
            r"create.*window.*": ["winuser"],
            # More GDI functions - EXPANDED
            r"^getstockobject$": ["wingdi"],  # GetStockObject specifically
            r"^deletedc$": ["wingdi"],  # DeleteDC specifically
            r"^createdc$": ["wingdi"],  # CreateDC specifically
            r"^createcompatibledc$": ["wingdi"],  # CreateCompatibleDC specifically
            r"^selectobject$": ["wingdi"],  # SelectObject specifically
            r"^deleteobject$": ["wingdi"],  # DeleteObject specifically
            r"^bitblt$": ["wingdi"],  # BitBlt specifically
            r"^stretchblt$": ["wingdi"],  # StretchBlt specifically
            r"^textout$": ["wingdi"],  # TextOut specifically
            r"^drawtext$": ["wingdi"],  # DrawText specifically
            r".*stock.*": ["wingdi"],
            r"delete.*": ["wingdi", "fileapi"],
            r".*dc.*": ["wingdi"],
            r".*brush.*": ["wingdi"],
            r".*font.*": ["wingdi"],
            # CRITICAL FUNCTIONS - SPECIFIC MAPPINGS
            r"^enumprocesses$": ["psapi"],  # EnumProcesses specifically
            r"^createtoolhelp32snapshot$": [
                "tlhelp32"
            ],  # CreateToolhelp32Snapshot specifically
            r"^urldownloadtofile$": ["urlmon"],  # URLDownloadToFile specifically
            r"^urldownloadtofilea$": ["urlmon"],  # URLDownloadToFileA specifically
            r"^urldownloadtofilew$": ["urlmon"],  # URLDownloadToFileW specifically
            r"^winhttpopenrequest$": ["winhttp"],  # WinHttpOpenRequest specifically
            r"^winhttpopen$": ["winhttp"],  # WinHttpOpen specifically
            r"^winhttpconnect$": ["winhttp"],  # WinHttpConnect specifically
            r"^ftpputfile$": ["wininet"],  # FtpPutFile specifically
            r"^ftpputfilea$": ["wininet"],  # FtpPutFileA specifically
            r"^ftpputfilew$": ["wininet"],  # FtpPutFileW specifically
            # COMPREHENSIVE NATIVE API COVERAGE - ALL NT*/ZW* FUNCTIONS
            # File System Native APIs
            r"^(nt|zw)createfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)openfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)readfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)writefile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)deletefile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)queryinformationfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)setinformationfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)queryattributesfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)queryfullattributesfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)queryvolumeinformationfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)setvolumeinformationfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)flushinstructioncache$": ["wdm", "winternl"],
            r"^(nt|zw)lockfile$": ["wdm", "ntifs", "winternl"],
            r"^(nt|zw)unlockfile$": ["wdm", "ntifs", "winternl"],
            # Memory Management Native APIs
            r"^(nt|zw)allocatevirtualmemory$": ["wdm", "winternl"],
            r"^(nt|zw)freevirtualmemory$": ["wdm", "winternl"],
            r"^(nt|zw)protectvirtualmemory$": ["wdm", "winternl"],
            r"^(nt|zw)queryvirtualmemory$": ["wdm", "winternl"],
            r"^(nt|zw)readvirtualmemory$": ["wdm", "winternl"],
            r"^(nt|zw)writevirtualmemory$": ["wdm", "winternl"],
            r"^(nt|zw)mapviewofsection$": ["wdm", "winternl"],
            r"^(nt|zw)unmapviewofsection$": ["wdm", "winternl"],
            r"^(nt|zw)createsection$": ["wdm", "winternl"],
            r"^(nt|zw)opensection$": ["wdm", "winternl"],
            r"^(nt|zw)extendsection$": ["wdm", "winternl"],
            r"^(nt|zw)querysection$": ["wdm", "winternl"],
            r"^(nt|zw)flushmappedfiles$": ["wdm", "winternl"],
            # Process/Thread Native APIs
            r"^(nt|zw)createprocess$": ["wdm", "winternl"],
            r"^(nt|zw)createprocessex$": ["wdm", "winternl"],
            r"^(nt|zw)openprocess$": ["wdm", "winternl"],
            r"^(nt|zw)terminateprocess$": ["wdm", "winternl"],
            r"^(nt|zw)suspendprocess$": ["wdm", "winternl"],
            r"^(nt|zw)resumeprocess$": ["wdm", "winternl"],
            r"^(nt|zw)queryinformationprocess$": ["wdm", "winternl"],
            r"^(nt|zw)setinformationprocess$": ["wdm", "winternl"],
            r"^(nt|zw)createthread$": ["wdm", "winternl"],
            r"^(nt|zw)createthreadex$": ["wdm", "winternl"],
            r"^(nt|zw)openthread$": ["wdm", "winternl"],
            r"^(nt|zw)terminatethread$": ["wdm", "winternl"],
            r"^(nt|zw)suspendthread$": ["wdm", "winternl"],
            r"^(nt|zw)resumethread$": ["wdm", "winternl"],
            r"^(nt|zw)alertthread$": ["wdm", "winternl"],
            r"^(nt|zw)alertresumethread$": ["wdm", "winternl"],
            r"^(nt|zw)getcontextthread$": ["wdm", "winternl"],
            r"^(nt|zw)setcontextthread$": ["wdm", "winternl"],
            r"^(nt|zw)queryinformationthread$": ["wdm", "winternl"],
            r"^(nt|zw)setinformationthread$": ["wdm", "winternl"],
            r"^(nt|zw)queueapcthread$": ["wdm", "winternl"],
            r"^(nt|zw)testAlert$": ["wdm", "winternl"],
            # Object Manager Native APIs
            r"^(nt|zw)createevent$": ["wdm", "winternl"],
            r"^(nt|zw)openevent$": ["wdm", "winternl"],
            r"^(nt|zw)setevent$": ["wdm", "winternl"],
            r"^(nt|zw)resetevent$": ["wdm", "winternl"],
            r"^(nt|zw)pulseevent$": ["wdm", "winternl"],
            r"^(nt|zw)queryevent$": ["wdm", "winternl"],
            r"^(nt|zw)createmutant$": ["wdm", "winternl"],
            r"^(nt|zw)openmutant$": ["wdm", "winternl"],
            r"^(nt|zw)releasemutant$": ["wdm", "winternl"],
            r"^(nt|zw)querymutant$": ["wdm", "winternl"],
            r"^(nt|zw)createsemaphore$": ["wdm", "winternl"],
            r"^(nt|zw)opensemaphore$": ["wdm", "winternl"],
            r"^(nt|zw)releasesemaphore$": ["wdm", "winternl"],
            r"^(nt|zw)querysemaphore$": ["wdm", "winternl"],
            r"^(nt|zw)createtimer$": ["wdm", "winternl"],
            r"^(nt|zw)opentimer$": ["wdm", "winternl"],
            r"^(nt|zw)settimer$": ["wdm", "winternl"],
            r"^(nt|zw)canceltimer$": ["wdm", "winternl"],
            r"^(nt|zw)querytimer$": ["wdm", "winternl"],
            r"^(nt|zw)createjobobject$": ["wdm", "winternl"],
            r"^(nt|zw)openjobobject$": ["wdm", "winternl"],
            r"^(nt|zw)assignprocesstojobobject$": ["wdm", "winternl"],
            r"^(nt|zw)terminatejobobject$": ["wdm", "winternl"],
            r"^(nt|zw)queryinformationjobobject$": ["wdm", "winternl"],
            r"^(nt|zw)setinformationjobobject$": ["wdm", "winternl"],
            # Registry Native APIs
            r"^(nt|zw)createkey$": ["wdm", "winternl"],
            r"^(nt|zw)openkey$": ["wdm", "winternl"],
            r"^(nt|zw)openkeytransacted$": ["wdm", "winternl"],
            r"^(nt|zw)deletekey$": ["wdm", "winternl"],
            r"^(nt|zw)deletevaluekey$": ["wdm", "winternl"],
            r"^(nt|zw)enumeratekey$": ["wdm", "winternl"],
            r"^(nt|zw)enumeratevaluekey$": ["wdm", "winternl"],
            r"^(nt|zw)flushkey$": ["wdm", "winternl"],
            r"^(nt|zw)loadkey$": ["wdm", "winternl"],
            r"^(nt|zw)loadkey2$": ["wdm", "winternl"],
            r"^(nt|zw)loadkeyex$": ["wdm", "winternl"],
            r"^(nt|zw)notifychangekey$": ["wdm", "winternl"],
            r"^(nt|zw)notifychangemultiplekeys$": ["wdm", "winternl"],
            r"^(nt|zw)querykey$": ["wdm", "winternl"],
            r"^(nt|zw)queryvaluekey$": ["wdm", "winternl"],
            r"^(nt|zw)querymultiplevaluekey$": ["wdm", "winternl"],
            r"^(nt|zw)replacekey$": ["wdm", "winternl"],
            r"^(nt|zw)restorekey$": ["wdm", "winternl"],
            r"^(nt|zw)savekey$": ["wdm", "winternl"],
            r"^(nt|zw)savekeyex$": ["wdm", "winternl"],
            r"^(nt|zw)savemergedkeys$": ["wdm", "winternl"],
            r"^(nt|zw)setvaluekey$": ["wdm", "winternl"],
            r"^(nt|zw)unloadkey$": ["wdm", "winternl"],
            r"^(nt|zw)unloadkey2$": ["wdm", "winternl"],
            r"^(nt|zw)unloadkeyex$": ["wdm", "winternl"],
            # Security Native APIs
            r"^(nt|zw)accesscheck$": ["wdm", "winternl"],
            r"^(nt|zw)accesscheckandauditalarm$": ["wdm", "winternl"],
            r"^(nt|zw)accesscheckbytype$": ["wdm", "winternl"],
            r"^(nt|zw)accesscheckbytypeandauditalarm$": ["wdm", "winternl"],
            r"^(nt|zw)adjustgroupstoken$": ["wdm", "winternl"],
            r"^(nt|zw)adjustprivilegestoken$": ["wdm", "winternl"],
            r"^(nt|zw)compareTokens$": ["wdm", "winternl"],
            r"^(nt|zw)createtoken$": ["wdm", "winternl"],
            r"^(nt|zw)duplicatetoken$": ["wdm", "winternl"],
            r"^(nt|zw)filtertoken$": ["wdm", "winternl"],
            r"^(nt|zw)impersonateclientofport$": ["wdm", "winternl"],
            r"^(nt|zw)openprocesstoken$": ["wdm", "winternl"],
            r"^(nt|zw)openprocesstokenex$": ["wdm", "winternl"],
            r"^(nt|zw)openthreadtoken$": ["wdm", "winternl"],
            r"^(nt|zw)openthreadtokenex$": ["wdm", "winternl"],
            r"^(nt|zw)privilegecheck$": ["wdm", "winternl"],
            r"^(nt|zw)queryinformationtoken$": ["wdm", "winternl"],
            r"^(nt|zw)setinformationtoken$": ["wdm", "winternl"],
            r"^(nt|zw)setthreadtoken$": ["wdm", "winternl"],
            # System Information Native APIs
            r"^(nt|zw)querysysteminformation$": ["wdm", "winternl"],
            r"^(nt|zw)setsysteminformation$": ["wdm", "winternl"],
            r"^(nt|zw)querydefaultlocale$": ["wdm", "winternl"],
            r"^(nt|zw)setdefaultlocale$": ["wdm", "winternl"],
            r"^(nt|zw)querydefaultuilanguage$": ["wdm", "winternl"],
            r"^(nt|zw)setdefaultuilanguage$": ["wdm", "winternl"],
            r"^(nt|zw)queryinstalluilanguage$": ["wdm", "winternl"],
            r"^(nt|zw)querysystemtime$": ["wdm", "winternl"],
            r"^(nt|zw)setsystemtime$": ["wdm", "winternl"],
            r"^(nt|zw)querytimerresolution$": ["wdm", "winternl"],
            r"^(nt|zw)settimerresolution$": ["wdm", "winternl"],
            r"^(nt|zw)delayexecution$": ["wdm", "winternl"],
            r"^(nt|zw)yieldexecution$": ["wdm", "winternl"],
            # Generic Object Native APIs
            r"^(nt|zw)close$": ["wdm", "winternl"],
            r"^(nt|zw)duplicateobject$": ["wdm", "winternl"],
            r"^(nt|zw)queryobject$": ["wdm", "winternl"],
            r"^(nt|zw)setinformationobject$": ["wdm", "winternl"],
            r"^(nt|zw)queryinformationobject$": ["wdm", "winternl"],
            r"^(nt|zw)querysecurityobject$": ["wdm", "winternl"],
            r"^(nt|zw)setsecurityobject$": ["wdm", "winternl"],
            r"^(nt|zw)maketemporaryobject$": ["wdm", "winternl"],
            r"^(nt|zw)makepermanentobject$": ["wdm", "winternl"],
            r"^(nt|zw)signalAnDwaitforsingleobject$": ["wdm", "winternl"],
            r"^(nt|zw)waitforsingleobject$": ["wdm", "winternl"],
            r"^(nt|zw)waitformultipleobjects$": ["wdm", "winternl"],
            r"^(nt|zw)waitformultipleobjects32$": ["wdm", "winternl"],
            # COMPREHENSIVE RTL RUNTIME LIBRARY FUNCTIONS
            r"^rtlinitansistring$": ["winternl", "ntddk"],
            r"^rtlinitunicodestring$": ["winternl", "ntddk"],
            r"^rtlinitString$": ["winternl", "ntddk"],
            r"^rtlfreeAnsistring$": ["winternl", "ntddk"],
            r"^rtlfreuUnicodestring$": ["winternl", "ntddk"],
            r"^rtlfreestring$": ["winternl", "ntddk"],
            r"^rtlcopyansistring$": ["winternl", "ntddk"],
            r"^rtlcopyunicodestring$": ["winternl", "ntddk"],
            r"^rtlcopystring$": ["winternl", "ntddk"],
            r"^rtlAnsistring^Tounicodestring$": ["winternl", "ntddk"],
            r"^rtlunicodestringa^Toansistring$": ["winternl", "ntddk"],
            r"^rtlunicodestring^Tointeger$": ["winternl", "ntddk"],
            r"^rtlinteger^Tounicodestring$": ["winternl", "ntddk"],
            r"^rtlcompareAnsistring$": ["winternl", "ntddk"],
            r"^rtlcompareunicodestring$": ["winternl", "ntddk"],
            r"^rtlequAnsistring$": ["winternl", "ntddk"],
            r"^rtleunicodestring$": ["winternl", "ntddk"],
            r"^rtlPrefixAnsistring$": ["winternl", "ntddk"],
            r"^rtlprefixunicodestring$": ["winternl", "ntddk"],
            r"^rtlupperAnsistring$": ["winternl", "ntddk"],
            r"^rtlupperunicodestring$": ["winternl", "ntddk"],
            r"^rtldowncaseunicestring$": ["winternl", "ntddk"],
            r"^rtlAppendansistring^Tostring$": ["winternl", "ntddk"],
            # RTL Exception/Unwinding functions - DOCUMENTED
            r"^rtllookupfunctionentry$": [
                "winnt"
            ],  # RtlLookupFunctionEntry specifically
            r"^rtlvirtualunwind$": ["winnt"],  # RtlVirtualUnwind specifically
            r"^rtladdfunctiontable$": ["winnt"],  # RtlAddFunctionTable specifically
            r"^rtldeletefunctiontable$": [
                "winnt"
            ],  # RtlDeleteFunctionTable specifically
            r"^rtlinstallfunctiontablecallback$": [
                "winnt"
            ],  # RtlInstallFunctionTableCallback specifically
            r"^rtlrestorecontext$": ["winnt"],  # RtlRestoreContext specifically
            r"^rtlunwind$": ["winnt"],  # RtlUnwind specifically
            r"^rtlunwind2$": ["winnt"],  # RtlUnwind2 specifically
            r"^rtlunwindex$": ["winnt"],  # RtlUnwindEx specifically
            # RTL Memory functions - DDK/WDM DOCUMENTED
            r"^rtlzeromemory$": ["wdm"],  # RtlZeroMemory - DDK documented
            r"^rtlmovememory$": ["wdm"],  # RtlMoveMemory - DDK documented
            r"^rtlcopymemory$": ["wdm"],  # RtlCopyMemory - DDK documented
            r"^rtlcomparememory$": ["wdm"],  # RtlCompareMemory - DDK documented
            r"^rtlfillmemory$": ["wdm"],  # RtlFillMemory - DDK documented
            r"^rtlappensui$": ["winternl", "ntddk"],
            # RTL Memory Management
            r"^rtlallocateheap$": ["winternl", "ntddk"],
            r"^rtlfreeheap$": ["winternl", "ntddk"],
            r"^rtlcreateheap$": ["winternl", "ntddk"],
            r"^rtldestroyheap$": ["winternl", "ntddk"],
            r"^rtlsizeheap$": ["winternl", "ntddk"],
            r"^rtlvalidateheap$": ["winternl", "ntddk"],
            r"^rtlreAllocateheap$": ["winternl", "ntddk"],
            r"^rtlcompactheap$": ["winternl", "ntddk"],
            r"^rtllockheap$": ["winternl", "ntddk"],
            r"^rtlunlockheap$": ["winternl", "ntddk"],
            r"^rtlfillmemory$": ["winternl", "ntddk"],
            r"^rtlmovememory$": ["winternl", "ntddk"],
            r"^rtlcomparememory$": ["winternl", "ntddk"],
            r"^rtlcopybytes$": ["winternl", "ntddk"],
            r"^rtlsecurezeromemory$": ["winternl", "ntddk"],
            # RTL Critical Section and Synchronization
            r"^rtlinitializecriticalsection$": ["winternl", "ntddk"],
            r"^rtldeletecriticalsection$": ["winternl", "ntddk"],
            r"^rtlentercriticalsection$": ["winternl", "ntddk"],
            r"^rtlleavecriticalsection$": ["winternl", "ntddk"],
            r"^rtltrycriticalsection$": ["winternl", "ntddk"],
            r"^rtlinitializecriticalsectionAndspincount$": ["winternl", "ntddk"],
            r"^rtlsetcriticalsectionspincount$": ["winternl", "ntddk"],
            r"^rtlcreateuserthead$": ["winternl", "ntddk"],
            r"^rtlexitusertehead$": ["winternl", "ntddk"],
            r"^rtlremoteusertread$": ["winternl", "ntddk"],
            r"^rtlisthread^Terminating$": ["winternl", "ntddk"],
            # RTL Path and Environment
            r"^rtlgetcurrentdirectory$": ["winternl", "ntddk"],
            r"^rtlsetcurrentdirectory$": ["winternl", "ntddk"],
            r"^rtlgetfullpathname$": ["winternl", "ntddk"],
            r"^rtldospathnametonpath^Name$": ["winternl", "ntddk"],
            r"^rtldeterminedospathnameype$": ["winternl", "ntddk"],
            r"^rtlisDosDevicename$": ["winternl", "ntddk"],
            r"^rtlgetlonPpathname$": ["winternl", "ntddk"],
            r"^rtlgetshortpathname$": ["winternl", "ntddk"],
            r"^rtlqueryen^Tvironmentvariable$": ["winternl", "ntddk"],
            r"^rtlsetenv$": ["winternl", "ntddk"],
            r"^rtlsetenvironmentvariable$": ["winternl", "ntddk"],
            r"^rtlexpandenvironmentstings$": ["winternl", "ntddk"],
            r"^rtlcreateenvironment$": ["winternl", "ntddk"],
            r"^rtlDestroyenvironment$": ["winternl", "ntddk"],
            # RTL Time and Conversion
            r"^rtlsystemtimetolocaltime$": ["winternl", "ntddk"],
            r"^rtllocaltimetosystemtime$": ["winternl", "ntddk"],
            r"^rtltimetotime^Fields$": ["winternl", "ntddk"],
            r"^rtltimeieldstode$": ["winternl", "ntddk"],
            r"^rtltimetoseconds$": ["winternl", "ntddk"],
            r"^rtlsecondstoe$": ["winternl", "ntddk"],
            r"^rtlquerytime^Zone$": ["winternl", "ntddk"],
            r"^rtlrandom$": ["winternl", "ntddk"],
            r"^rtlrandomex$": ["winternl", "ntddk"],
            r"^rtluniform$": ["winternl", "ntddk"],
            # LDR DYNAMIC LOADER FUNCTIONS
            r"^ldrloaddll$": ["winternl", "ntddk"],
            r"^ldrunloaddll$": ["winternl", "ntddk"],
            r"^ldrgetprocedureaddress$": ["winternl", "ntddk"],
            r"^ldrgetdllhandle$": ["winternl", "ntddk"],
            r"^ldrgetdllhandleex$": ["winternl", "ntddk"],
            r"^ldrqueriyimagefileexecutionoptions$": ["winternl", "ntddk"],
            r"^ldrfindentryforaddress$": ["winternl", "ntddk"],
            r"^ldrfindresource$": ["winternl", "ntddk"],
            r"^ldrfindresourceex$": ["winternl", "ntddk"],
            r"^ldraccessresource$": ["winternl", "ntddk"],
            r"^ldrfindresourcediretory$": ["winternl", "ntddk"],
            r"^ldrenumeratesources$": ["winternl", "ntddk"],
            r"^ldrenumerareresourcenames$": ["winternl", "ntddk"],
            r"^ldrenumerateresourcelanguages$": ["winternl", "ntddk"],
            r"^ldrprocessrAlocationblock$": ["winternl", "ntddk"],
            r"^ldrverifyourrimage^Inmemor$": ["winternl", "ntddk"],
            r"^ldrlockloaderlock$": ["winternl", "ntddk"],
            r"^ldrunlockloaderlock$": ["winternl", "ntddk"],
            r"^ldrreelocation^Block$": ["winternl", "ntddk"],
            # Toolhelp functions
            r".*toolhelp.*": ["tlhelp32"],
            r".*snapshot.*": ["tlhelp32"],
            r"^process32first$": ["tlhelp32"],  # Process32First specifically
            r"^process32next$": ["tlhelp32"],  # Process32Next specifically
            r"^thread32first$": ["tlhelp32"],  # Thread32First specifically
            r"^thread32next$": ["tlhelp32"],  # Thread32Next specifically
            r"^module32first$": ["tlhelp32"],  # Module32First specifically
            r"^module32next$": ["tlhelp32"],  # Module32Next specifically
            # PSAPI functions
            r".*processes$": ["psapi"],
            r"enum.*": ["psapi", "winreg", "commctrl"],
            # URLMon functions - SPECIAL LEGACY PATH
            r"^urldownloadtofile$": ["urlmon"],  # Special handling needed
            r"url.*": ["urlmon"],
            r".*download.*": ["urlmon"],
            # WinHTTP functions
            r"winhttp.*": ["winhttp"],
            r"http.*": ["winhttp", "wininet"],
            # FTP functions
            r"ftp.*": ["wininet"],
        }

    def generate_possible_urls(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
    ) -> List[str]:
        """
        Generate all possible URLs for a function based on patterns

        Args:
            function_name: Name of the Win32 function
            dll_name: DLL containing the function (if known)
            base_url: Base Microsoft Learn URL

        Returns:
            List of possible URLs in order of probability
        """
        function_lower = function_name.lower()
        urls = []

        # 0. ML-based header predictions (HIGHEST priority if available)
        ml_headers = []
        if self.ml_classifier and self.ml_classifier.is_trained:
            try:
                ml_predictions = self.ml_classifier.predict_headers(
                    function_name, dll_name, top_k=3
                )
                ml_headers = [
                    header for header, confidence in ml_predictions if confidence > 0.1
                ]
            except Exception:
                pass  # Continue without ML if it fails

        # 1. Check for DLL-specific primary header first (high priority)
        priority_headers = []
        if dll_name and dll_name.lower() in self.dll_to_primary_header:
            primary_header = self.dll_to_primary_header[dll_name.lower()]
            priority_headers.append(primary_header)

        # 2. Get headers based on function name patterns
        pattern_headers = []
        for pattern, pattern_header_list in self.function_patterns.items():
            if re.match(pattern, function_lower):
                pattern_headers.extend(pattern_header_list)

        # 3. Get headers based on DLL (secondary priority)
        dll_headers = []
        if dll_name:
            dll_headers = self.dll_to_headers.get(dll_name.lower(), [])

        # 4. Add common fallback headers (lowest priority)
        common_headers = [
            "winbase",
            "winuser",
            "fileapi",
            "memoryapi",
            "processthreadsapi",
        ]

        # Combine in order of priority (ML first!)
        all_headers = (
            ml_headers
            + priority_headers
            + pattern_headers
            + dll_headers
            + common_headers
        )

        # Remove duplicates while preserving order
        headers_to_try = []
        seen = set()
        for header in all_headers:
            if header not in seen:
                headers_to_try.append(header)
                seen.add(header)
            # Limit to max 8 headers to prevent infinite generation
            if len(headers_to_try) >= 8:
                break

        # 4. Generate URLs for each header
        for header in headers_to_try:
            # Standard pattern: header/nf-header-function
            url_path = f"{header}/nf-{header}-{function_lower}"
            full_url = f"{base_url}/windows/win32/api/{url_path}"
            urls.append(full_url)

            # Try with explicit A/W suffixes if function doesn't have them
            if not function_lower.endswith(("a", "w")):
                # Try with A suffix (most common)
                url_path_a = f"{header}/nf-{header}-{function_lower}a"
                full_url_a = f"{base_url}/windows/win32/api/{url_path_a}"
                urls.append(full_url_a)

                # Try with W suffix
                url_path_w = f"{header}/nf-{header}-{function_lower}w"
                full_url_w = f"{base_url}/windows/win32/api/{url_path_w}"
                urls.append(full_url_w)

            # Try without 'A' or 'W' suffix if function ends with them
            elif function_lower.endswith(("a", "w")):
                base_func = function_lower[:-1]
                url_path = f"{header}/nf-{header}-{base_func}"
                full_url = f"{base_url}/windows/win32/api/{url_path}"
                urls.append(full_url)

        # 4.5. Special legacy functions with known URLs
        if function_lower == "urldownloadtofile":
            # URLDownloadToFile has a special legacy URL
            legacy_url = "https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/platform-apis/ms775123(v=vs.85)"
            urls.insert(0, legacy_url)  # Insert at beginning for highest priority

        elif function_lower == "ftpputfile":
            # FtpPutFile works with A suffix
            ftp_url = f"{base_url}/windows/win32/api/wininet/nf-wininet-ftpputfilea"
            urls.insert(0, ftp_url)

        # 5. Native API functions - prioritize WDK documentation paths with Nt<->Zw mapping
        if function_lower.startswith(("nt", "zw", "rtl", "ke", "mm")):
            # Native API functions are primarily documented in WDK paths
            driver_headers = ["wdm", "ntifs", "ntddk", "winternl", "ntdef"]

            # Create both Nt and Zw variants for testing
            native_variants = [function_lower]
            if function_lower.startswith("nt"):
                # Try Zw variant (most common in documentation)
                zw_variant = "zw" + function_lower[2:]
                native_variants.insert(0, zw_variant)  # Prioritize Zw variant
            elif function_lower.startswith("zw"):
                # Try Nt variant
                nt_variant = "nt" + function_lower[2:]
                native_variants.append(nt_variant)

            # Test both variants against all driver headers
            for variant in native_variants:
                for header in driver_headers:
                    url_path = f"{header}/nf-{header}-{variant}"
                    full_url = f"{base_url}/windows-hardware/drivers/ddi/{url_path}"
                    urls.insert(0, full_url)  # Insert at beginning for highest priority

            # Also try winternl for some documented Native API functions
            for variant in native_variants:
                url_path = f"winternl/nf-winternl-{variant}"
                full_url = f"{base_url}/windows/win32/api/{url_path}"
                urls.append(full_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def generate_all_possible_urls(
        self, function_name: str, base_url: str = "https://learn.microsoft.com/en-us"
    ) -> List[Tuple[str, str, str]]:
        """Generate ALL possible URLs for Elite coverage (URL, locale, area)"""
        urls = []
        symbol_lower = function_name.lower()

        # INTELLIGENT HEADER PRIORITY: Use patterns first, then fallback to common headers
        pattern_headers = []
        for pattern, pattern_header_list in self.function_patterns.items():
            if re.match(pattern, symbol_lower):
                pattern_headers.extend(pattern_header_list)

        # Remove duplicates while preserving order
        intelligent_headers = []
        seen = set()
        for header in pattern_headers:
            if header not in seen:
                intelligent_headers.append(header)
                seen.add(header)

        # Headers COMPLETOS - TODOS os headers do Windows SDK DRASTICAMENTE EXPANDIDOS
        common_headers = [
            # CORE SYSTEM APIs (MÁXIMA prioridade)
            "winuser",
            "wingdi",
            "winbase",
            "fileapi",
            "memoryapi",
            "processthreadsapi",
            "handleapi",
            "synchapi",
            "errhandlingapi",
            "debugapi",
            "libloaderapi",
            "heapapi",
            "processenv",
            "sysinfoapi",
            "consoleapi",
            "profileapi",
            # PROCESS & THREAD APIs EXPANDIDOS
            "processthreadsapi",
            "securitybaseapi",
            "userenv",
            "psapi",
            "toolhelp",
            "tlhelp32",
            "jobapi",
            "jobapi2",
            "threadpoollegacyapiset",
            "fibersapi",
            "processenv",
            "wow64apiset",
            "processthreadsapi",
            "handleapi",
            # ADVANCED SYSTEM APIs EXPANDIDOS
            "realtimeapiset",
            "interlockedapi",
            "securityappcontainer",
            "systemtopologyapi",
            "utilapiset",
            "ioapiset",
            "namedpipeapi",
            "namespaceapi",
            "winsafer",
            "securitybaseapi",
            "authz",
            "accctrl",
            "errhandlingapi",
            "debugapi",
            # SECURITY & CRYPTO COMPLETE
            "aclapi",
            "wincrypt",
            "bcrypt",
            "ncrypt",
            "wincred",
            "winefs",
            "wintrust",
            "sspi",
            "schannel",
            "ntsecapi",
            "dpapi",
            "cryptuiapi",
            "credui",
            "lsalookup",
            "secext",
            "secedit",
            "winscard",
            "wintrust",
            "certadm",
            "certcli",
            "certenc",
            "certenroll",
            "certpol",
            "certsrv",
            "certview",
            "xenroll",
            # REGISTRY & SERVICES COMPLETE
            "winreg",
            "winsvc",
            "evntprov",
            "evntrace",
            "perflib",
            "pdh",
            "loadperf",
            "winperf",
            "evntcons",
            "evntrace",
            "tdh",
            "wmistr",
            "wmium",
            # NETWORKING COMPLETE
            "winsock2",
            "winsock",
            "ws2tcpip",
            "wsipx",
            "mswsock",
            "ws2spi",
            "wininet",
            "urlmon",
            "winhttp",
            "winnetwk",
            "npapi",
            "snmp",
            "winsnmp",
            "iphlpapi",
            "iprtrmib",
            "iptypes",
            "icmpapi",
            "netioapi",
            "tcpestats",
            "udpmib",
            "tcpmib",
            "ifmib",
            "ipmib",
            "dhcpcsdk",
            "dhcpsapi",
            # UI & SHELL COMPLETE
            "commctrl",
            "commdlg",
            "shellapi",
            "shlobj",
            "shlwapi",
            "shobjidl",
            "uxtheme",
            "vsstyle",
            "vssym32",
            "dwmapi",
            "windowsandmessaging",
            "menurc",
            "winstation",
            "prsht",
            "richedit",
            "richole",
            "textserv",
            "dde",
            "ddeml",
            "msaatext",
            "oleacc",
            "winable",
            "wincon",
            # MULTIMEDIA & DEVICES COMPLETE
            "mmsystem",
            "mmreg",
            "timeapi",
            "playsoundapi",
            "winspool",
            "wingdi",
            "setupapi",
            "cfgmgr32",
            "devguid",
            "regstr",
            "powrprof",
            "batclass",
            "devpkey",
            "dbt",
            "hidclass",
            "hidpi",
            "hidsdi",
            "hidusage",
            "newdev",
            "pnputil",
            "sporder",
            "spapidef",
            "sputils",
            "swdevice",
            "usbioctl",
            "usbiodef",
            "usbuser",
            "winioctl",
            "winusb",
            "devioctl",
            "poclass",
            # COM & OLE COMPLETE
            "combaseapi",
            "objbase",
            "objidl",
            "unknwn",
            "wtypes",
            "oaidl",
            "activation",
            "callobj",
            "cguid",
            "comcat",
            "comdefsp",
            "coml2api",
            "compobj",
            "comsvcs",
            "docobj",
            "dvdmedia",
            "exdisp",
            "hlink",
            "htiface",
            "htiframe",
            "htmlhelp",
            "hyptrk",
            "iaccessible",
            "mshtmhst",
            "mshtml",
            "mshtmdid",
            "msxml",
            "ocidl",
            "olectl",
            "oledlg",
            "oleauto",
            "oleidl",
            "propidl",
            "propsys",
            "propvarutil",
            "servprov",
            "shlguid",
            "strmif",
            "structuredquery",
            "tom",
            "txfw32",
            "urlhist",
            "urlmon",
            "webservices",
            "wia",
            "wincodec",
            "wincodecsdk",
            # RPC & IPC COMPLETE
            "rpc",
            "rpcdce",
            "rpcndr",
            "rpcproxy",
            "rpcasync",
            "rpcdcep",
            "rpcnsi",
            "rpcnterr",
            "rpcssl",
            "midles",
            "midluser",
            # NETWORK MANAGEMENT COMPLETE
            "lmaccess",
            "lmapibuf",
            "lmconfig",
            "lmerr",
            "lmserver",
            "lmshare",
            "lmuse",
            "lmwksta",
            "netapi32",
            "lmat",
            "lmcons",
            "lmstats",
            "lmalert",
            "lmaudit",
            "lmmsg",
            "lmremutl",
            "lmrepl",
            "lmsname",
            # DEBUG & TOOLS COMPLETE
            "imagehlp",
            "dbghelp",
            "fci",
            "fdi",
            "dbgeng",
            "cor",
            "corsym",
            "corprof",
            "cordebug",
            "metahost",
            "mscoree",
            "fusion",
            "clrdata",
            "diasdk",
            "cvconst",
            "dbgmodel",
            "engextcpp",
            "extsfns",
            "wdbgexts",
            # NATIVE/INTERNAL COMPLETE
            "winternl",
            "ntstatus",
            "subauth",
            "winnt",
            "ntdef",
            "ntlsa",
            "ntsecapi",
            "ntddndis",
            "ntdddisk",
            "ntddkbd",
            "ntddmou",
            "ntddpar",
            "ntddscsi",
            "ntddser",
            "ntddstor",
            "ntddtape",
            "ntddvol",
            "ntimage",
            "ntldr",
            # VERSION & TIME COMPLETE
            "winver",
            "timezoneapi",
            "versionhelpers",
            "verrsrc",
            # CRT & STANDARD COMPLETE
            "corecrt",
            "crtdbg",
            "malloc",
            "stdio",
            "stdlib",
            "string",
            "time",
            "crtasm",
            "direct",
            "dos",
            "fcntl",
            "io",
            "memory",
            "process",
            "search",
            "share",
            "signal",
            "sys",
            "wchar",
            # WINDOWS RUNTIME & MODERN APIs
            "roapi",
            "robuffer",
            "roerrorapi",
            "rometadata",
            "rometadataapi",
            "rometadataresolution",
            "roparameterizediid",
            "roregistrationapi",
            "winrt",
            "activation",
            "asyncinfo",
            "eventtoken",
            "hstring",
            "inspectable",
            "memorybuffer",
            "restrictederrorinfo",
            "shcore",
            "windows",
            # AUDIO & VIDEO
            "audioclient",
            "audiopolicy",
            "devicetopology",
            "endpointvolume",
            "mmdeviceapi",
            "mmreg",
            "dsound",
            "dshow",
            "dxva2",
            "evr",
            "mfapi",
            "mferror",
            "mfidl",
            "mfobjects",
            "mfplay",
            "mfreadwrite",
            "mftransform",
            "wmcodecdsp",
            "wmcontainer",
            "wmsdkidl",
            "wmsdk",
            # GRAPHICS & DIRECTX
            "d2d1",
            "d2d1helper",
            "d3d9",
            "d3d10",
            "d3d11",
            "d3d12",
            "d3dcompiler",
            "dwrite",
            "dxgi",
            "dxgiformat",
            "dxgidebug",
            "dxgitype",
            "ddraw",
            "gdiplus",
            "gdiplusheaders",
            "gdiplusimaging",
            "gdipluslinecaps",
            "gdipluspixelformats",
            "gdiplustypes",
            "uianimation",
            "wincodec",
            "wincodecsdk",
            "d2d1effects",
            "d2d1svg",
            "d3d11on12",
            "d3d12sdklayers",
            # GAME DEVELOPMENT
            "xinput",
            "xaudio2",
            "x3daudio",
            "xapofx",
            "gamemode",
            # PRINTING
            "winspool",
            "compstui",
            "winddiui",
            "printoem",
            "prcomoem",
            # ACCESSIBILITY
            "oleacc",
            "uiautomation",
            "uiautomationcore",
            "uiautomationcoreapi",
            "winable",
        ]

        # Combine: intelligent headers FIRST, then common headers as fallback
        all_headers = intelligent_headers + [h for h in common_headers if h not in seen]

        # WDK/DDI headers
        ddi_headers = ["ntifs", "ntddk", "wdm", "winternl", "ntdef"]

        # Both locales
        locales = ["pt-br", "en-us"] if "/pt-br" in base_url else ["en-us", "pt-br"]

        for locale in locales:
            # Try Win32 SDK patterns - INTELLIGENT HEADERS FIRST!
            for header in all_headers:
                base_api_url = (
                    f"https://learn.microsoft.com/{locale}/windows/win32/api/{header}"
                )

                # Function patterns
                urls.append(
                    (f"{base_api_url}/nf-{header}-{symbol_lower}", locale, "SDK")
                )
                urls.append(
                    (f"{base_api_url}/nf-{header}-{symbol_lower}a", locale, "SDK")
                )
                urls.append(
                    (f"{base_api_url}/nf-{header}-{symbol_lower}w", locale, "SDK")
                )

                # Struct patterns
                urls.append(
                    (f"{base_api_url}/ns-{header}-{symbol_lower}", locale, "SDK")
                )

                # Enum patterns
                urls.append(
                    (f"{base_api_url}/ne-{header}-{symbol_lower}", locale, "SDK")
                )

                # Interface patterns
                urls.append(
                    (f"{base_api_url}/nn-{header}-{symbol_lower}", locale, "SDK")
                )

            # Try WDK/DDI patterns for Native API
            for header in ddi_headers:
                base_ddi_url = f"https://learn.microsoft.com/{locale}/windows-hardware/drivers/ddi/{header}"

                urls.append(
                    (f"{base_ddi_url}/nf-{header}-{symbol_lower}", locale, "DDI")
                )
                urls.append(
                    (f"{base_ddi_url}/ns-{header}-{symbol_lower}", locale, "DDI")
                )
                urls.append(
                    (f"{base_ddi_url}/ne-{header}-{symbol_lower}", locale, "DDI")
                )

        return urls

    def get_random_headers(self) -> Dict[str, str]:
        """Get intelligent User-Agent and headers based on success rates"""

        # Intelligent user agent selection
        user_agent = self._get_optimal_user_agent()
        additional = random.choice(self.additional_headers)
        self._request_counter += 1
        self._requests_with_current_agent += 1

        # Base headers optimized for Microsoft Learn
        headers = {
            "User-Agent": user_agent,
            **additional,
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Add modern browser headers for better success rate
        headers.update(
            {
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            }
        )

        # Randomly vary some headers to appear more natural
        if random.random() < 0.4:
            headers["Cache-Control"] = "max-age=0"

        if random.random() < 0.3:
            headers["Accept-Language"] = "en-US,en;q=0.5"

        return headers

    def _get_optimal_user_agent(self) -> str:
        """Select user agent based on success statistics and rotation strategy"""

        # If we've made too many requests with current agent, rotate
        if self._requests_with_current_agent >= self._max_requests_per_agent:
            self._rotate_user_agent()

        # Use last successful agent if available and not overused
        if (
            self._last_successful_agent
            and self._requests_with_current_agent < self._max_requests_per_agent
        ):
            return self._last_successful_agent

        # Get highest success rate agents first
        if self.user_agent_stats:
            sorted_agents = sorted(
                self.user_agent_stats.items(),
                key=lambda x: x[1].get("success_rate", 0.5),
                reverse=True,
            )

            # Use top 3 agents and rotate between them
            top_agents = [agent for agent, _ in sorted_agents[:3]]
            if top_agents:
                return top_agents[self._current_rotation_index % len(top_agents)]

        # Fallback to prioritized categories for Microsoft Learn
        priority_categories = ["chrome_win", "firefox_win", "edge_win", "chrome_mac"]

        for category in priority_categories:
            if category in self.user_agents:
                agents = self.user_agents[category]
                return agents[self._current_rotation_index % len(agents)]

        # Final fallback
        return self.user_agents_flat[
            self._current_rotation_index % len(self.user_agents_flat)
        ]

    def _rotate_user_agent(self):
        """Rotate to next user agent"""
        self._current_rotation_index = (self._current_rotation_index + 1) % len(
            self.user_agents_flat
        )
        self._requests_with_current_agent = 0

    def _extract_header_from_url(self, url: str) -> Optional[str]:
        """Extract header name from a successful URL for ML training"""
        try:
            # URL format: /windows/win32/api/HEADER/nf-HEADER-functionname
            if "/api/" in url:
                parts = url.split("/api/")
                if len(parts) > 1:
                    header_part = parts[1].split("/")[0]
                    return header_part
        except Exception:
            pass
        return None

    def report_user_agent_success(self, user_agent: str, success: bool):
        """Track user agent success for intelligent rotation"""
        if user_agent not in self.user_agent_stats:
            self.user_agent_stats[user_agent] = {
                "total_requests": 0,
                "successful_requests": 0,
                "success_rate": 0.5,
                "last_used": time.time(),
            }

        stats = self.user_agent_stats[user_agent]
        stats["total_requests"] += 1
        stats["last_used"] = time.time()

        if success:
            stats["successful_requests"] += 1
            self._last_successful_agent = user_agent
            # Reset failure count on success
            self._agent_failure_count[user_agent] = 0
        else:
            # Track failures
            self._agent_failure_count[user_agent] = (
                self._agent_failure_count.get(user_agent, 0) + 1
            )

        # Update success rate
        stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]

        # If agent fails too much, rotate immediately
        if self._agent_failure_count.get(user_agent, 0) >= 3:
            self._rotate_user_agent()

    def _should_attempt_request(self) -> bool:
        """Check circuit breaker state to determine if request should be attempted"""
        current_time = time.time()
        breaker = self._circuit_breaker

        if breaker["state"] == "OPEN":
            # Check if recovery timeout has passed
            if (
                current_time - breaker["last_failure_time"]
                > breaker["recovery_timeout"]
            ):
                breaker["state"] = "HALF_OPEN"
                return True
            return False

        return True  # CLOSED or HALF_OPEN

    def _record_success(self):
        """Record successful request for circuit breaker"""
        breaker = self._circuit_breaker

        if breaker["state"] == "HALF_OPEN":
            breaker["consecutive_successes_needed"] -= 1
            if breaker["consecutive_successes_needed"] <= 0:
                breaker["state"] = "CLOSED"
                breaker["failure_count"] = 0
                breaker["consecutive_successes_needed"] = 2
        elif breaker["state"] == "CLOSED":
            breaker["failure_count"] = max(0, breaker["failure_count"] - 1)

    def _record_failure(self):
        """Record failed request for circuit breaker"""
        breaker = self._circuit_breaker
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()

        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["state"] = "OPEN"

    def _record_rate_limit(self):
        """Record rate limit response"""
        # Rate limits are treated less severely than failures
        breaker = self._circuit_breaker
        breaker["failure_count"] += 0.5  # Half weight for rate limits
        breaker["last_failure_time"] = time.time()

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate adaptive retry delay with jitter"""
        config = self._retry_config

        # Exponential backoff
        delay = min(
            config["base_delay"] * (config["backoff_factor"] ** (attempt - 1)),
            config["max_delay"],
        )

        # Add jitter to avoid thundering herd
        if config["jitter"]:
            jitter = delay * 0.1 * random.random()  # ±10% jitter
            delay += jitter

        return delay

    async def _request_with_retry(
        self, session, url: str, base_headers: Dict[str, str]
    ) -> Optional[str]:
        """Make request with intelligent retry logic"""

        for attempt in range(self._retry_config["max_retries"] + 1):
            if not self._should_attempt_request():
                return None

            try:
                if attempt > 0:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)

                # Refresh headers for each attempt
                headers = (
                    base_headers.copy() if attempt == 0 else self.get_random_headers()
                )

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        self._record_success()
                        self.report_user_agent_success(
                            headers.get("User-Agent", ""), True
                        )

                        # Ultra-fast content check
                        content_chunk = await response.content.read(1024)
                        content_str = content_chunk.decode(
                            "utf-8", errors="ignore"
                        ).lower()

                        if any(
                            keyword in content_str
                            for keyword in [
                                "function",
                                "routine",
                                "api",
                                "syntax",
                                "parameters",
                            ]
                        ):
                            return url

                    elif response.status == 429:  # Rate limited
                        self._record_rate_limit()
                        if attempt < self._retry_config["max_retries"]:
                            continue

                    elif response.status >= 500:  # Server error
                        self._record_failure()
                        if attempt < self._retry_config["max_retries"]:
                            continue

                    # Non-retryable or final attempt
                    self.report_user_agent_success(headers.get("User-Agent", ""), False)
                    return None

            except Exception:
                self._record_failure()
                self.report_user_agent_success(headers.get("User-Agent", ""), False)

                if attempt < self._retry_config["max_retries"]:
                    continue
                return None

            except Exception:
                if attempt < self._retry_config["max_retries"]:
                    continue
                return None

        return None

    async def find_valid_url_async(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
        session=None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """
        ULTRA-FAST async method with intelligent prioritization and early termination.
        Uses hybrid approach: high-confidence URLs first, then broader search if needed.
        """
        # Lazy import aiohttp
        import aiohttp

        # Generate smart prioritized URLs
        prioritized_urls = self._get_prioritized_urls(function_name, dll_name, base_url)

        # Test high-confidence URLs first (top 8-12)
        high_confidence_urls = prioritized_urls[:12]

        if session:
            # Try high-confidence URLs with faster method
            result = await self._test_urls_fast_batch(
                high_confidence_urls, session, progress_callback
            )

            # If not found and function is important, try more URLs
            if not result and (dll_name or self._is_important_function(function_name)):
                remaining_urls = prioritized_urls[12:25]
                result = await self._test_urls_sequential(
                    remaining_urls, session, progress_callback
                )

            return result
        else:
            # Optimized session for maximum speed
            connector = None
            temp_session = None

            try:
                connector = aiohttp.TCPConnector(
                    limit=8,
                    limit_per_host=4,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    keepalive_timeout=30,
                )
                timeout = aiohttp.ClientTimeout(total=8, connect=3)
                temp_session = aiohttp.ClientSession(
                    connector=connector, timeout=timeout
                )

                result = await self._test_urls_fast_batch(
                    high_confidence_urls, temp_session, progress_callback
                )

                if not result and (
                    dll_name or self._is_important_function(function_name)
                ):
                    remaining_urls = prioritized_urls[12:25]
                    result = await self._test_urls_sequential(
                        remaining_urls, temp_session, progress_callback
                    )

                return result
            finally:
                # Close session first, then connector
                if temp_session and not temp_session.closed:
                    await temp_session.close()
                if connector and not connector.closed:
                    await connector.close()

    def _get_prioritized_urls(
        self, function_name: str, dll_name: str, base_url: str
    ) -> list:
        """Get URLs in optimal priority order for fastest discovery with AI learning"""
        # Use the corrected generate_possible_urls method which has all the fixes
        return self.generate_possible_urls(function_name, dll_name, base_url)

    def _is_important_function(self, function_name: str) -> bool:
        """Determine if function is important enough for extended search"""
        function_lower = function_name.lower()
        important_patterns = [
            r"^create.*",
            r"^get.*",
            r"^set.*",
            r"^open.*",
            r"^close.*",
            r"^read.*",
            r"^write.*",
            r"^nt.*",
            r"^zw.*",
        ]
        return any(re.match(pattern, function_lower) for pattern in important_patterns)

    async def _test_urls_fast_batch(
        self,
        urls: List[str],
        session,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """Fast batch testing with optimized concurrency and early termination"""

        async def test_single_url_fast(url: str, delay: float = 0.0) -> Optional[str]:
            # Check circuit breaker state
            if not self._should_attempt_request():
                return None

            headers = None
            for attempt in range(self._retry_config["max_retries"] + 1):
                try:
                    if delay > 0 or attempt > 0:
                        retry_delay = (
                            delay
                            if attempt == 0
                            else self._calculate_retry_delay(attempt)
                        )
                        await asyncio.sleep(retry_delay)

                    headers = self.get_random_headers()

                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            # Success - update circuit breaker and user agent stats
                            self._record_success()
                            if headers:
                                self.report_user_agent_success(
                                    headers.get("User-Agent", ""), True
                                )

                            # Minimal content check for speed
                            content_type = response.headers.get(
                                "Content-Type", ""
                            ).lower()
                            if "html" in content_type:
                                content_chunk = await response.content.read(2048)
                                content_str = content_chunk.decode(
                                    "utf-8", errors="ignore"
                                ).lower()
                                if any(
                                    keyword in content_str
                                    for keyword in [
                                        "function",
                                        "syntax",
                                        "parameters",
                                        "api",
                                    ]
                                ):
                                    return url

                        elif response.status == 429:  # Rate limited
                            self._record_rate_limit()
                            if attempt < self._retry_config["max_retries"]:
                                continue  # Retry with longer delay

                        elif response.status >= 500:  # Server error
                            if attempt < self._retry_config["max_retries"]:
                                continue  # Retry server errors

                        # Non-retryable status or final attempt
                        if headers:
                            self.report_user_agent_success(
                                headers.get("User-Agent", ""), False
                            )
                        return None

                except Exception as e:
                    self._record_failure()
                    if headers:
                        self.report_user_agent_success(
                            headers.get("User-Agent", ""), False
                        )

                    if attempt < self._retry_config["max_retries"]:
                        continue  # Retry on client errors
                    return None

                except Exception:
                    if attempt < self._retry_config["max_retries"]:
                        continue  # Retry on unexpected errors
                    return None

            return None

        # Create staggered tasks to avoid overwhelming the server
        tasks = []
        for i, url in enumerate(urls):
            delay = i * 0.1  # 100ms delay between requests
            task = asyncio.create_task(test_single_url_fast(url, delay))
            tasks.append(task)

        # Use as_completed for early termination
        total = len(tasks)
        completed = 0

        try:
            for completed_task in asyncio.as_completed(tasks):
                try:
                    result = await completed_task
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, total)

                    if (
                        result
                    ):  # Found valid URL - cancel remaining and return immediately
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        return result

                except Exception:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
                    continue
        finally:
            # Clean up any remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for cancelled tasks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        return None

    async def _test_urls_sequential(
        self,
        urls: List[str],
        session,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """Test URLs sequentially with optimized speed and smart delays"""

        total = len(urls)
        consecutive_failures = 0

        for i, url in enumerate(urls, 1):
            try:
                if progress_callback:
                    progress_callback(i, total)

                # Adaptive delay based on failure rate
                if i > 1:
                    if consecutive_failures > 2:
                        delay = random.uniform(0.5, 1.0)  # Longer delay after failures
                    else:
                        delay = random.uniform(0.1, 0.3)  # Shorter delay for speed
                    await asyncio.sleep(delay)

                headers = self.get_random_headers()

                result = await self._request_with_retry(session, url, headers)
                if result:
                    return result
                consecutive_failures += 1

            except Exception:
                consecutive_failures += 1
                continue

        return None

    async def _test_urls_async(
        self,
        urls: List[str],
        session,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """Test multiple URLs concurrently and return first valid one"""

        async def test_single_url(url: str) -> Optional[str]:
            try:
                # Use random headers for each request
                headers = self.get_random_headers()
                # Random delay to avoid rate limiting and appear more human
                delay = random.uniform(0.1, 0.4)
                await asyncio.sleep(delay)
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # Quick content check to ensure it's a valid function page
                        content = await response.text()
                        if any(
                            keyword in content.lower()
                            for keyword in [
                                "function",
                                "routine",
                                "api",
                                "syntax",
                                "parameters",
                            ]
                        ):
                            return url
                    return None
            except:
                return None

        # Create tasks for ALL URLs simultaneously
        tasks = [test_single_url(url) for url in urls]
        total = len(tasks)
        completed = 0

        # Use as_completed to get the FIRST successful result
        # Capture parameters for closures
        fn_name, dll = function_name, dll_name
        
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                if result:  # Found valid URL!
                    # Record success for pattern learning
                    try:
                        # Lazy load pattern learner only when needed
                        try:
                            from .url_pattern_learner import pattern_learner

                            pattern_learner.record_success(
                                fn_name, result, dll or ""
                            )
                        except ImportError:
                            pass  # Pattern learner is optional
                    except Exception:
                        pass  # Don't fail on learning errors

                    # Train ML classifier with successful mapping
                    if self.ml_classifier:
                        try:
                            # Extract header from successful URL for training
                            url_header = self._extract_header_from_url(result)
                            if url_header:
                                self.ml_classifier.add_training_example(
                                    fn_name, url_header, dll or "", success=True
                                )
                        except Exception:
                            pass  # Don't fail on ML training errors

                    # Cancel remaining tasks for speed
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    return result
            except:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                continue

        return None  # No valid URL found

    def find_valid_url_sync(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
        max_workers: int = 12,  # Reduced for better performance
    ) -> Optional[str]:
        """
        Optimized synchronous version with intelligent URL prioritization
        Tests prioritized URLs first for maximum speed
        """
        import requests

        # Get prioritized URLs instead of all URLs
        prioritized_urls = self._get_prioritized_urls(function_name, dll_name, base_url)

        # Test high-confidence URLs first
        high_confidence_urls = prioritized_urls[:15]

        def test_url_fast(url: str) -> Optional[str]:
            try:
                headers = self.get_random_headers()
                # Reduced timeout for speed
                response = requests.get(url, headers=headers, timeout=2.5)

                if response.status_code == 200:
                    # Fast content check - only first 1KB
                    content_chunk = (
                        response.content[:1024].decode("utf-8", errors="ignore").lower()
                    )
                    if any(
                        keyword in content_chunk
                        for keyword in [
                            "function",
                            "routine",
                            "api",
                            "syntax",
                            "parameters",
                        ]
                    ):
                        return url
                return None
            except Exception:
                return None

        # First round: Test high-confidence URLs
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(test_url_fast, url): url for url in high_confidence_urls
            }

            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    if result:
                        # Cancel remaining futures and return immediately
                        for remaining_future in future_to_url:
                            if not remaining_future.done():
                                remaining_future.cancel()
                        return result
                except Exception:
                    continue

        # Second round: If not found and function is important, try more URLs
        if self._is_important_function(function_name) and len(prioritized_urls) > 15:
            remaining_urls = prioritized_urls[15:25]

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(test_url_fast, url): url for url in remaining_urls
                }

                for future in as_completed(future_to_url):
                    try:
                        result = future.result()
                        if result:
                            for remaining_future in future_to_url:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            return result
                    except Exception:
                        continue

        return None

    def get_high_probability_urls(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
    ) -> List[str]:
        """
        Get only the most likely URLs (top 15) for better Native API coverage
        """
        all_urls = self.generate_possible_urls(function_name, dll_name, base_url)
        return all_urls[:15]  # Return top 15 to cover Zw variants

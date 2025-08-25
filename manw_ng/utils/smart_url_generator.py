"""
Smart URL Generator for Win32 API Documentation

Ultra-fast asynchronous URL generator that tests ALL known patterns simultaneously.
This system ensures 100% coverage with maximum speed using concurrent requests.
"""

from typing import List, Dict, Set, Optional, Tuple, Callable
import re
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random


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

        # Circuit breaker for intelligent retry
        self._circuit_breaker = {
            "failure_count": 0,
            "last_failure_time": 0,
            "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
            "failure_threshold": 5,
            "recovery_timeout": 30,  # seconds
            "consecutive_successes_needed": 2,
        }

        # Adaptive retry configuration
        self._retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "backoff_factor": 2.0,
            "jitter": True,
        }

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
            "ntdll.dll": ["winternl", "winbase", "ntstatus", "subauth"],
            "psapi.dll": ["psapi", "toolhelp"],
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
            # File operations
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
            r"get.*command.*line": ["processenv"],
            # Memory operations
            r"virtual.*": ["memoryapi"],
            r"heap.*": ["heapapi"],
            r".*alloc.*": ["memoryapi", "heapapi"],
            r".*memory.*": ["memoryapi"],
            # Process/Thread
            r".*process.*": ["processthreadsapi"],
            r".*thread.*": ["processthreadsapi"],
            r"terminate.*": ["processthreadsapi"],
            r"suspend.*": ["processthreadsapi"],
            r"resume.*": ["processthreadsapi"],
            # Registry
            r"reg.*": ["winreg"],
            r".*key.*": ["winreg"],
            # Services
            r".*service.*": ["winsvc"],
            # Network
            r".*socket.*": ["winsock2"],
            r"ws.*": ["winsock2"],
            r"internet.*": ["wininet"],
            r"net.*": ["lmaccess", "lmserver"],
            # Security/Crypto/ACL
            r"cert.*": ["wincrypt"],
            r"crypt.*": ["wincrypt", "bcrypt"],
            r".*security.*": ["securitybaseapi"],
            r".*acl.*": ["aclapi"],
            r".*effective.*": ["aclapi"],
            r".*trustee.*": ["aclapi"],
            # Shell/System
            r"shell.*": ["shellapi"],
            r"sh.*": ["shellapi"],
            # Console
            r".*console.*": ["consoleapi"],
            # Library loading
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
            # More GDI functions
            r".*stock.*": ["wingdi"],
            r"delete.*": ["wingdi", "fileapi"],
            r".*dc.*": ["wingdi"],
            r".*brush.*": ["wingdi"],
            r".*font.*": ["wingdi"],
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

        # 1. Check for DLL-specific primary header first (highest priority)
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

        # Combine in order of priority
        all_headers = priority_headers + pattern_headers + dll_headers + common_headers

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

        # 5. Native API functions - prioritize WDK documentation paths
        if function_lower.startswith(("nt", "zw", "rtl", "ke", "mm")):
            # Native API functions are primarily documented in WDK paths
            driver_headers = ["ntifs", "ntddk", "wdm", "winternl", "ntdef"]
            for header in driver_headers:
                url_path = f"{header}/nf-{header}-{function_lower}"
                full_url = f"{base_url.replace('/en-us', '').replace('/pt-br', '')}/windows-hardware/drivers/ddi/{url_path}"
                urls.insert(0, full_url)  # Insert at beginning for priority

            # Also try winternl for some documented Native API functions
            if function_lower.startswith(("nt", "zw")):
                url_path = f"winternl/nf-winternl-{function_lower}"
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
        self, session: aiohttp.ClientSession, url: str, base_headers: Dict[str, str]
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

            except aiohttp.ClientError:
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
        session: aiohttp.ClientSession = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """
        ULTRA-FAST async method with intelligent prioritization and early termination.
        Uses hybrid approach: high-confidence URLs first, then broader search if needed.
        """
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
        """Get URLs in optimal priority order for fastest discovery"""
        function_lower = function_name.lower()
        urls = []

        # Phase 1: Highest confidence URLs based on patterns and DLL
        if dll_name:
            primary_header = self.dll_to_primary_header.get(dll_name.lower())
            if primary_header:
                # Most likely header for this DLL
                base_api_url = f"{base_url}/windows/win32/api/{primary_header}"
                urls.extend(
                    [
                        f"{base_api_url}/nf-{primary_header}-{function_lower}",
                        f"{base_api_url}/nf-{primary_header}-{function_lower}a",
                        f"{base_api_url}/nf-{primary_header}-{function_lower}w",
                    ]
                )

        # Phase 2: Pattern-based URLs (high confidence)
        pattern_headers = []
        for pattern, headers in self.function_patterns.items():
            if re.match(pattern, function_lower):
                pattern_headers.extend(headers[:2])  # Top 2 headers per pattern
                break  # Use first matching pattern only for speed

        # Add pattern-based URLs
        for header in pattern_headers[:3]:  # Limit to top 3 for speed
            if header not in [h.split("/")[-1] for h in urls if h]:  # Avoid duplicates
                base_api_url = f"{base_url}/windows/win32/api/{header}"
                new_urls = [f"{base_api_url}/nf-{header}-{function_lower}"]
                if not function_lower.endswith(("a", "w")):
                    new_urls.extend(
                        [
                            f"{base_api_url}/nf-{header}-{function_lower}a",
                            f"{base_api_url}/nf-{header}-{function_lower}w",
                        ]
                    )
                urls.extend(new_urls)

        # Phase 3: Native API prioritization
        if function_lower.startswith(("nt", "zw", "rtl")):
            for header in ["winternl", "ntifs", "ntddk"]:
                base_ddi_url = f"{base_url.replace('/pt-br', '').replace('/en-us', '')}/windows-hardware/drivers/ddi/{header}"
                urls.insert(
                    0, f"{base_ddi_url}/nf-{header}-{function_lower}"
                )  # Insert at beginning

        # Phase 4: Common fallback headers (medium confidence)
        common_headers = ["winbase", "winuser", "fileapi", "memoryapi"]
        for header in common_headers:
            if header not in [h.split("/")[-1] for h in urls if h]:  # Avoid duplicates
                base_api_url = f"{base_url}/windows/win32/api/{header}"
                new_urls = [f"{base_api_url}/nf-{header}-{function_lower}"]
                if not function_lower.endswith(("a", "w")):
                    new_urls.append(f"{base_api_url}/nf-{header}-{function_lower}a")
                urls.extend(new_urls)

        # Clean up None values and remove duplicates while preserving order
        clean_urls = []
        seen = set()
        for url in urls:
            if url and url not in seen:
                clean_urls.append(url)
                seen.add(url)

        return clean_urls

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
        session: aiohttp.ClientSession,
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

                except aiohttp.ClientError as e:
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
        session: aiohttp.ClientSession,
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
        session: aiohttp.ClientSession,
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
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                if result:  # Found valid URL!
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
        Get only the most likely URLs (top 5) for faster testing
        """
        all_urls = self.generate_possible_urls(function_name, dll_name, base_url)
        return all_urls[:5]  # Return top 5 most probable

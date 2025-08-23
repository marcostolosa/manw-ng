"""
Win32 API URL Pattern Discovery System
====================================

Baseado na pesquisa extensa de padrões de URL do Microsoft Learn.
Implementa heurística robusta para nunca mais falhar na busca de documentação.
"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

# Padrões expandidos para cobertura completa de todos os tipos de símbolos
EXTENDED_PATTERNS = {
    "win32_functions": [
        "windows/win32/api/{header}/nf-{header}-{symbol}",
        "windows/win32/api/{header}/nf-{header}-{symbol_lower}",
    ],
    "structures": [
        "windows/win32/api/{header}/ns-{header}-{symbol}",
        "windows/win32/api/{header}/ns-{header}-{symbol_lower}",
        "windows/win32/api/winternl/ns-winternl-{symbol_lower}",
    ],
    "enums": [
        "windows/win32/api/{header}/ne-{header}-{symbol}",
        "windows/win32/api/{header}/ne-{header}-{symbol_lower}",
    ],
    "callbacks": [
        "windows/win32/api/{header}/nc-{header}-{symbol}",
        "windows/win32/api/{header}/nc-{header}-{symbol_lower}",
    ],
    "com_interfaces": [
        "windows/win32/api/{header}/nn-{header}-{symbol}",
        "windows/win32/api/{header}/nn-{header}-{symbol_lower}",
    ],
    "printdocs": [
        "windows/win32/printdocs/{symbol}",
        "windows/win32/printdocs/{symbol_lower}",
    ],
    "native_api": [
        "windows/win32/api/winternl/nf-winternl-{symbol_lower}",
        "windows-hardware/drivers/ddi/{header}/nf-{header}-{symbol_lower}",
        "windows-hardware/drivers/ddi/ntifs/nf-ntifs-{symbol_lower}",
        "windows-hardware/drivers/ddi/wdm/nf-wdm-{symbol_lower}",
        "windows-hardware/drivers/ddi/ntddk/nf-ntddk-{symbol_lower}",
        "windows-hardware/drivers/ddi/fltkernel/nf-fltkernel-{symbol_lower}",
    ],
}

# Headers específicos por categoria
NATIVE_API_HEADERS = ["ntifs", "wdm", "ntddk", "fltkernel", "winternl"]
MULTIMEDIA_HEADERS = ["mmiscapi", "mmeapi", "timeapi", "mmreg", "winmm"]
COM_HEADERS = ["objidl", "shobjidl", "comcat", "unknwn", "oleidl"]
PRINT_HEADERS = ["winspool", "wingdi"]

# Mapeamento de estruturas conhecidas para headers
STRUCTURE_TO_HEADER = {
    "peb": "winternl",
    "teb": "winternl",
    "token_control": "winternl",
    "process_basic_information": "winternl",
    "unicode_string": "winternl",
    "object_attributes": "winternl",
    "io_status_block": "winternl",
    "client_id": "winternl",
    "curdir": "winternl",
    "rtl_user_process_parameters": "winternl",
}

# Mapeamento de callbacks conhecidos
CALLBACK_TO_HEADER = {
    "wndproc": "winuser",
    "enumwindowsproc": "winuser",
    "hookproc": "winuser",
    "timerproc": "winuser",
    "enumresnameproc": "winbase",
}


class Win32URLPatterns:
    """Sistema de descoberta de URLs baseado em padrões do Microsoft Learn"""

    # Mapeamento header -> módulo baseado na análise
    HEADER_TO_MODULE = {
        # File I/O APIs
        "fileapi.h": "fileapi",
        "winbase.h": "winbase",
        # Memory APIs
        "memoryapi.h": "memoryapi",
        "heapapi.h": "heapapi",
        # Process/Thread APIs
        "processthreadsapi.h": "processthreadsapi",
        # Window/User APIs
        "winuser.h": "winuser",
        # Graphics/GDI APIs
        "wingdi.h": "wingdi",
        # Registry APIs
        "winreg.h": "winreg",
        # Network APIs
        "winsock.h": "winsock",
        "winsock2.h": "winsock2",
        "ws2tcpip.h": "winsock2",
        "wininet.h": "wininet",
        # Library loading APIs
        "libloaderapi.h": "libloaderapi",
        # System APIs
        "sysinfoapi.h": "sysinfoapi",
        "errhandlingapi.h": "errhandlingapi",
        "securitybaseapi.h": "securitybaseapi",
        "handleapi.h": "handleapi",
        "debugapi.h": "debugapi",
        "profileapi.h": "profileapi",
        "timeapi.h": "timeapi",
        "synchapi.h": "synchapi",
        # Console APIs
        "consoleapi.h": "consoleapi",
        "consoleapi2.h": "consoleapi2",
        "consoleapi3.h": "consoleapi3",
        # Comm/Device APIs
        "commapi.h": "winbase",  # Often grouped under winbase
        # Crypto APIs
        "wincrypt.h": "wincrypt",
        # Service APIs
        "winsvc.h": "winsvc",
        # Shell APIs
        "shellapi.h": "shellapi",
        "shlobj.h": "shlobj_core",
        # COM APIs
        "objbase.h": "objbase",
        "combaseapi.h": "combaseapi",
        # RTL/NT APIs
        "winternl.h": "winternl",
        "ntifs.h": "ntifs",
        "wdm.h": "wdm",
        "ntddk.h": "ntddk",
        # Version APIs
        "winver.h": "winver",
        # DLL APIs
        "psapi.h": "psapi",
        "tlhelp32.h": "tlhelp32",
        # Security APIs
        "aclapi.h": "aclapi",
        "authz.h": "authz",
        "lmaccess.h": "lmaccess",
        # Power APIs
        "powrprof.h": "powrprof",
        "winnt.h": "winnt",
        # DirectX APIs
        "d3d11.h": "d3d11",
        "d3d12.h": "d3d12",
        "d3dcompiler.h": "d3dcompiler",
        "dxgi.h": "dxgi",
        # Shell APIs Extended
        "shlwapi.h": "shlwapi",
        "shcore.h": "shcore",
        "shlobj_core.h": "shlobj_core",
    }

    # Mapeamento function -> module conhecido (casos especiais)
    FUNCTION_TO_MODULE = {
        # File operations
        "createfilea": "fileapi",
        "createfilew": "fileapi",
        "readfile": "fileapi",
        "writefile": "fileapi",
        "createdirectorya": "fileapi",
        "createdirectoryw": "fileapi",
        "deletefilea": "fileapi",
        "deletefilew": "fileapi",
        # Memory operations
        "virtualalloc": "memoryapi",
        "virtualallocex": "memoryapi",
        "virtualfree": "memoryapi",
        "readprocessmemory": "memoryapi",
        "writeprocessmemory": "memoryapi",
        "heapalloc": "heapapi",
        "heapfree": "heapapi",
        "heapcreate": "heapapi",
        # Process/Thread operations
        "openprocess": "processthreadsapi",
        "createprocessa": "processthreadsapi",
        "createprocessw": "processthreadsapi",
        "createthread": "processthreadsapi",
        "createremotethread": "processthreadsapi",
        "terminateprocess": "processthreadsapi",
        "terminatethread": "processthreadsapi",
        "suspendthread": "processthreadsapi",
        "resumethread": "processthreadsapi",
        "getprocessid": "processthreadsapi",
        "getthreadid": "processthreadsapi",
        "getcurrentprocess": "processthreadsapi",
        "getcurrentthread": "processthreadsapi",
        # Window operations
        "messageboxa": "winuser",
        "messageboxw": "winuser",
        "createwindowa": "winuser",
        "createwindoww": "winuser",
        "createwindowexa": "winuser",
        "createwindowexw": "winuser",
        "setwindowshookexa": "winuser",
        "setwindowshookexw": "winuser",
        "sendmessage": "winuser",
        "sendmessagea": "winuser",
        "sendmessagew": "winuser",
        "postmessage": "winuser",
        "postmessagea": "winuser",
        "postmessagew": "winuser",
        "findwindowa": "winuser",
        "findwindoww": "winuser",
        "showwindow": "winuser",
        "setwindowtext": "winuser",
        "getwindowtext": "winuser",
        # Registry operations
        "regopenkeyexa": "winreg",
        "regopenkeyexw": "winreg",
        "regsetvalueexa": "winreg",
        "regsetvalueexw": "winreg",
        "regcreatekeyexa": "winreg",
        "regcreatekeyexw": "winreg",
        "regqueryvalueexa": "winreg",
        "regqueryvalueexw": "winreg",
        "regclosekey": "winreg",
        "regdeletekey": "winreg",
        "regdeletevalue": "winreg",
        # Network operations
        "socket": "winsock2",
        "connect": "winsock2",
        "bind": "winsock2",
        "listen": "winsock2",
        "accept": "winsock2",
        "send": "winsock2",
        "recv": "winsock2",
        "closesocket": "winsock2",
        "wsastartup": "winsock",
        "wsacleanup": "winsock",
        # Library loading
        "loadlibrarya": "libloaderapi",
        "loadlibraryw": "libloaderapi",
        "loadlibraryexa": "libloaderapi",
        "loadlibraryexw": "libloaderapi",
        "getprocaddress": "libloaderapi",
        "freelibrary": "libloaderapi",
        "getmodulehandlea": "libloaderapi",
        "getmodulehandlew": "libloaderapi",
        # Graphics/GDI
        "bitblt": "wingdi",
        "createcompatibledc": "wingdi",
        "createbitmap": "wingdi",
        "deletedc": "wingdi",
        "deleteobject": "wingdi",
        "selectobject": "wingdi",
        # Legacy operations
        "winexec": "winbase",
        "copyfile": "winbase",
        "movefile": "winbase",
        "getmodulefilename": "winbase",
        "gettemppath": "winbase",
        "getcomputername": "winbase",
        # Process environment
        "getcommandline": "processenv",
        "getcommandlinea": "processenv",
        "getcommandlinew": "processenv",
        # RTL functions
        "rtlallocateheap": "ntifs",
        "rtlfreeheap": "ntifs",
        "rtlcreateheap": "ntifs",
        "rtldestroyheap": "ntifs",
        "rtlcopymemory": "winternl",
        "rtlzeromemory": "winternl",
        "rtlmovememory": "winternl",
        # WinINet operations
        "internetopena": "wininet",
        "internetopenw": "wininet",
        "internetconnecta": "wininet",
        "internetconnectw": "wininet",
        "httpopenrequesta": "wininet",
        "httpopenrequestw": "wininet",
        "httpsendrequesta": "wininet",
        "httpsendrequestw": "wininet",
        "internetreadfile": "wininet",
        "internetwritefile": "wininet",
        "internetclosehandle": "wininet",
        "internetgetlastresponsinfo": "wininet",
        "internetqueryoptiona": "wininet",
        "internetqueryoptionw": "wininet",
        "internetsetoptiona": "wininet",
        "internetsetoptionw": "wininet",
        "ftpopenfilea": "wininet",
        "ftpopenfilew": "wininet",
        "ftpgetfilea": "wininet",
        "ftpgetfilew": "wininet",
        "ftpputfilea": "wininet",
        # DirectX APIs
        "d3d11createdevice": "d3d11",
        "d3d11createdeviceandswapchain": "d3d11",
        "d3d12createdevice": "d3d12",
        "dxgicreatefactory": "dxgi",
        # COM APIs
        "coinitialize": "combaseapi",
        "couninitialize": "combaseapi",
        "cocreateinstance": "combaseapi",
        "oleinitialize": "ole32",
        "oleuninitialize": "ole32",
        # Shell APIs Extended
        "shgetfolderpath": "shlobj_core",
        "shgetknownfolderpath": "shlobj_core",
        "shellexecutea": "shellapi",
        "shellexecutew": "shellapi",
        "ftpputfilew": "wininet",
    }

    # Prefixos de função que indicam o módulo
    MODULE_PREFIXES = {
        "rtl": ["ntifs", "winternl"],
        "nt": ["winternl", "ntifs"],
        "zw": ["winternl"],
        "wsa": ["winsock", "winsock2"],
        "reg": ["winreg"],
        "heap": ["heapapi"],
        "virtual": ["memoryapi"],
        "create": ["processthreadsapi", "winuser", "fileapi", "winbase"],
        "open": ["processthreadsapi", "fileapi", "winreg"],
        "read": ["fileapi", "memoryapi"],
        "write": ["fileapi", "memoryapi"],
        "get": ["winuser", "libloaderapi", "winbase", "sysinfoapi"],
        "set": ["winuser", "winreg", "winbase"],
        "find": ["winuser", "fileapi"],
        "load": ["libloaderapi"],
        "free": ["libloaderapi", "heapapi", "memoryapi"],
    }

    @classmethod
    def generate_url(cls, function_name: str, locale: str = "en-us") -> str:
        """
        Gera URL baseada nos padrões identificados

        Formato: https://learn.microsoft.com/{locale}/windows/win32/api/{module}/nf-{module}-{function}
        """
        function_lower = function_name.lower()
        module = cls.guess_module(function_name)

        if not module:
            # Fallback para tentativas com módulos comuns
            return None

        url = f"https://learn.microsoft.com/{locale}/windows/win32/api/{module}/nf-{module}-{function_lower}"
        return url

    @classmethod
    def generate_hardware_drivers_url(
        cls, function_name: str, locale: str = "en-us"
    ) -> str:
        """
        Gera URL para funções de drivers de hardware (RTL/NT)

        Formato: https://learn.microsoft.com/{locale}/windows-hardware/drivers/ddi/{module}/nf-{module}-{function}
        """
        function_lower = function_name.lower()

        # RTL functions geralmente estão em ntifs
        if function_lower.startswith("rtl"):
            module = "ntifs"
        elif function_lower.startswith("nt") or function_lower.startswith("zw"):
            module = "winternl"
        else:
            return None

        url = f"https://learn.microsoft.com/{locale}/windows-hardware/drivers/ddi/{module}/nf-{module}-{function_lower}"
        return url

    @classmethod
    def guess_module(cls, function_name: str) -> Optional[str]:
        """
        Adivinha o módulo baseado no nome da função
        """
        function_lower = function_name.lower()

        # Verificar mapeamento direto
        if function_lower in cls.FUNCTION_TO_MODULE:
            return cls.FUNCTION_TO_MODULE[function_lower]

        # Verificar prefixos
        for prefix, modules in cls.MODULE_PREFIXES.items():
            if function_lower.startswith(prefix):
                return modules[0]  # Retorna o primeiro módulo mais provável

        # Fallback para funções comuns
        if any(keyword in function_lower for keyword in ["process", "thread"]):
            return "processthreadsapi"
        elif any(
            keyword in function_lower for keyword in ["file", "directory", "folder"]
        ):
            return "fileapi"
        elif any(
            keyword in function_lower for keyword in ["memory", "virtual", "heap"]
        ):
            return "memoryapi" if "virtual" in function_lower else "heapapi"
        elif any(
            keyword in function_lower for keyword in ["window", "message", "hook"]
        ):
            return "winuser"
        elif any(keyword in function_lower for keyword in ["registry", "reg", "key"]):
            return "winreg"
        elif any(keyword in function_lower for keyword in ["socket", "wsa", "network"]):
            return "winsock2"
        elif any(
            keyword in function_lower for keyword in ["library", "module", "proc"]
        ):
            return "libloaderapi"

        return None

    @classmethod
    def get_all_possible_urls(
        cls, symbol_name: str, locale: str = "en-us"
    ) -> List[str]:
        """
        Gera todas as URLs possíveis para um símbolo (função, estrutura, enum, etc.)
        """
        urls = []

        # 1. URLs para funções (nf-)
        function_url = cls.generate_url(symbol_name, locale)
        if function_url:
            urls.append(function_url)

        # 2. URLs para estruturas (ns-)
        struct_url = cls.generate_structure_url(symbol_name, locale)
        if struct_url:
            urls.append(struct_url)

        # 3. URLs para enums (ne-)
        enum_url = cls.generate_enum_url(symbol_name, locale)
        if enum_url:
            urls.append(enum_url)

        # 4. URLs para callbacks (nc-)
        callback_url = cls.generate_callback_url(symbol_name, locale)
        if callback_url:
            urls.append(callback_url)

        # 5. URLs para interfaces COM (nn-)
        interface_url = cls.generate_interface_url(symbol_name, locale)
        if interface_url:
            urls.append(interface_url)

        # 6. URL para drivers de hardware (RTL/NT)
        hardware_url = cls.generate_hardware_drivers_url(symbol_name, locale)
        if hardware_url:
            urls.append(hardware_url)

        # 7. Variações A/W se o símbolo não tiver sufixo
        symbol_lower = symbol_name.lower()
        if not symbol_lower.endswith("a") and not symbol_lower.endswith("w"):
            # Tentar versão A
            url_a = cls.generate_url(symbol_name + "A", locale)
            if url_a:
                urls.append(url_a)

            # Tentar versão W
            url_w = cls.generate_url(symbol_name + "W", locale)
            if url_w:
                urls.append(url_w)

        # 8. Tentar com módulos alternativos baseado em prefixos
        guessed_module = cls.guess_module(symbol_name)
        if guessed_module:
            prefix = symbol_lower[:3]
            if prefix in cls.MODULE_PREFIXES:
                for alt_module in cls.MODULE_PREFIXES[prefix][
                    1:
                ]:  # Pular o primeiro (já tentado)
                    alt_url = f"https://learn.microsoft.com/{locale}/windows/win32/api/{alt_module}/nf-{alt_module}-{symbol_lower}"
                    urls.append(alt_url)

        return list(set(urls))  # Remove duplicatas

    @classmethod
    def classify_symbol_type(cls, symbol_name: str) -> str:
        """Classifica o tipo do símbolo baseado no padrão do nome"""
        symbol_lower = symbol_name.lower()

        # Native API
        if any(symbol_name.startswith(prefix) for prefix in ["Nt", "Zw", "Rtl", "Ldr"]):
            return "native_function"

        # Estruturas (geralmente UPPER_CASE ou conhecidas)
        if (
            symbol_name.isupper() and "_" in symbol_name
        ) or symbol_lower in STRUCTURE_TO_HEADER:
            return "structure"

        # Callbacks
        if (
            any(pattern in symbol_lower for pattern in ["proc", "callback", "hook"])
            or symbol_lower in CALLBACK_TO_HEADER
        ):
            return "callback"

        # COM Interfaces
        if (
            symbol_name.startswith("I")
            and len(symbol_name) > 1
            and symbol_name[1].isupper()
        ):
            return "com_interface"

        # Enums (frequentemente começam com maiúscula)
        if (
            symbol_name[0].isupper()
            and not any(c.islower() for c in symbol_name[:3])
            and "_" not in symbol_name
        ):
            return "enum"

        return "win32_function"

    @classmethod
    def generate_extended_urls(
        cls, symbol_name: str, locale: str = "en-us"
    ) -> List[str]:
        """
        Gera URLs usando os padrões expandidos baseado no tipo do símbolo
        """
        urls = []
        symbol_type = cls.classify_symbol_type(symbol_name)
        symbol_lower = symbol_name.lower()

        # Obter headers possíveis baseado no tipo e nome
        possible_headers = cls._get_possible_headers(symbol_name, symbol_type)

        # Gerar URLs baseado no tipo
        if symbol_type == "structure":
            patterns = EXTENDED_PATTERNS["structures"]
            for pattern in patterns:
                for header in possible_headers:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        header=header, symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

        elif symbol_type == "callback":
            patterns = EXTENDED_PATTERNS["callbacks"]
            for pattern in patterns:
                for header in possible_headers:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        header=header, symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

        elif symbol_type == "com_interface":
            patterns = EXTENDED_PATTERNS["com_interfaces"]
            for pattern in patterns:
                for header in possible_headers:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        header=header, symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

        elif symbol_type == "enum":
            patterns = EXTENDED_PATTERNS["enums"]
            for pattern in patterns:
                for header in possible_headers:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        header=header, symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

        elif symbol_type == "native_function":
            patterns = EXTENDED_PATTERNS["native_api"]
            for pattern in patterns:
                for header in possible_headers:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        header=header, symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

        else:  # win32_function
            patterns = EXTENDED_PATTERNS["win32_functions"]
            for pattern in patterns:
                for header in possible_headers:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        header=header, symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

            # Adicionar printdocs para funções que podem estar lá
            if any(
                keyword in symbol_lower for keyword in ["print", "spool", "doc", "page"]
            ):
                for pattern in EXTENDED_PATTERNS["printdocs"]:
                    url = f"https://learn.microsoft.com/{locale}/" + pattern.format(
                        symbol=symbol_name, symbol_lower=symbol_lower
                    )
                    urls.append(url)

        return list(set(urls))  # Remove duplicatas

    @classmethod
    def _get_possible_headers(cls, symbol_name: str, symbol_type: str) -> List[str]:
        """Retorna headers possíveis baseado no símbolo e tipo"""
        symbol_lower = symbol_name.lower()
        headers = []

        # Mapeamento direto primeiro
        if symbol_type == "structure" and symbol_lower in STRUCTURE_TO_HEADER:
            headers.append(STRUCTURE_TO_HEADER[symbol_lower])

        if symbol_type == "callback" and symbol_lower in CALLBACK_TO_HEADER:
            headers.append(CALLBACK_TO_HEADER[symbol_lower])

        # Headers baseado no tipo
        if symbol_type == "native_function":
            headers.extend(NATIVE_API_HEADERS)
        elif symbol_type == "com_interface":
            headers.extend(COM_HEADERS)
        elif symbol_type in ["structure", "callback"] and not headers:
            headers.extend(["winuser", "winbase", "winnt", "winternl"])

        # Headers baseado no prefixo da função
        if symbol_lower.startswith(("rtl", "nt", "zw")):
            headers.extend(NATIVE_API_HEADERS)
        elif any(keyword in symbol_lower for keyword in ["print", "spool"]):
            headers.extend(PRINT_HEADERS)
        elif any(keyword in symbol_lower for keyword in ["wave", "midi", "time", "mm"]):
            headers.extend(MULTIMEDIA_HEADERS)

        # Fallback para headers comuns se nenhum encontrado
        if not headers:
            headers = cls.get_common_modules()

        return list(set(headers))  # Remove duplicatas

    @classmethod
    def get_common_modules(cls) -> List[str]:
        """
        Retorna lista de módulos mais comuns para tentativas brutas
        """
        return [
            "processthreadsapi",
            "processenv",
            "fileapi",
            "memoryapi",
            "heapapi",
            "winuser",
            "winreg",
            "winsock2",
            "winsock",
            "libloaderapi",
            "winbase",
            "wingdi",
            "sysinfoapi",
            "errhandlingapi",
            "securitybaseapi",
            "handleapi",
            "debugapi",
            "profileapi",
            "timeapi",
            "synchapi",
            "consoleapi",
            "shellapi",
            "wincrypt",
            "winsvc",
            "ntifs",
            "winternl",
            "combaseapi",
            "wininet",
            "urlmon",
            "ole32",
            "oleaut32",
            "objbase",
            "activeds",
            "adshlp",
            "advpack",
            "authz",
            "cabinet",
            "cfgmgr32",
            "clusapi",
            "comctl32",
            "comdlg32",
            "compstui",
            "credui",
            "crypt32",
            "davclnt",
            "dbghelp",
            "ddeml",
            "d3d11",
            "d3d12",
            "d3dcompiler",
            "d3dx9",
            "d3dx10",
            "d3dx11",
            "dxgi",
            "shlwapi",
            "shcore",
            "shdocvw",
            "dhcpcsvc",
            "dinput",
            "dnsapi",
            "dwrite",
            "dwmapi",
            "fwpuclnt",
            "gdi32",
            "hid",
            "imm32",
            "iphlpapi",
            "kernel32",
            "ktmw32",
            "lz32",
            "mapi32",
            "mpr",
            "msimg32",
            "mswsock",
            "ncrypt",
            "netapi32",
            "newdev",
            "normaliz",
            "ntdsapi",
            "ntsecapi",
            "pdh",
            "powrprof",
            "psapi",
            "qwave",
            "rasapi32",
            "rasdlg",
            "resutils",
            "rpcrt4",
            "secur32",
            "sensapi",
            "setupapi",
            "sfc",
            "shell32",
            "shfolder",
            "snmpapi",
            "spoolss",
            "sti",
            "tapi32",
            "traffic",
            "userenv",
            "usp10",
            "uxtheme",
            "vfw32",
            "virtdisk",
            "wbemcli",
            "webservices",
            "wer",
            "wevtapi",
            "whttp",
            "wincodec",
            "wincred",
            "winhttp",
            "winmm",
            "winnls32",
            "winscard",
            "wintrust",
            "wlanapi",
            "wmi",
            "wtsapi32",
            "xinput",
        ]

    @classmethod
    def generate_structure_url(
        cls, struct_name: str, locale: str = "en-us"
    ) -> Optional[str]:
        """Gera URL para estruturas (ns- prefix)"""
        struct_lower = struct_name.lower()

        # Verificar se a estrutura está mapeada
        if struct_lower in cls.FUNCTION_TO_MODULE:
            module = cls.FUNCTION_TO_MODULE[struct_lower]
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/{module}/ns-{module}-{struct_lower}"

        # Para estruturas Native API (PEB, TEB, etc.)
        if struct_lower in [
            "peb",
            "teb",
            "kuser_shared_data",
        ] or struct_name.upper().endswith("_INFORMATION_CLASS"):
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/winternl/ns-winternl-{struct_lower}"

        # Tentar headers comuns para estruturas
        common_struct_headers = ["winuser", "winbase", "winnt", "winternl"]
        for header in common_struct_headers:
            url = f"https://learn.microsoft.com/{locale}/windows/win32/api/{header}/ns-{header}-{struct_lower}"
            # Note: idealmente verificaríamos se existe, mas por ora retornamos a primeira tentativa
            return url

        return None

    @classmethod
    def generate_enum_url(cls, enum_name: str, locale: str = "en-us") -> Optional[str]:
        """Gera URL para enums (ne- prefix)"""
        enum_lower = enum_name.lower()

        # Tentar headers baseados no nome do enum
        if "token" in enum_lower or "security" in enum_lower:
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/winnt/ne-winnt-{enum_lower}"
        elif "process" in enum_lower or "thread" in enum_lower:
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/processthreadsapi/ne-processthreadsapi-{enum_lower}"
        elif "file" in enum_lower or "dir" in enum_lower:
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/fileapi/ne-fileapi-{enum_lower}"
        else:
            # Fallback para winbase
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/winbase/ne-winbase-{enum_lower}"

    @classmethod
    def generate_callback_url(
        cls, callback_name: str, locale: str = "en-us"
    ) -> Optional[str]:
        """Gera URL para callbacks (nc- prefix)"""
        callback_lower = callback_name.lower()

        # A maioria dos callbacks está em winuser
        if (
            "proc" in callback_lower
            or "wnd" in callback_lower
            or "dlg" in callback_lower
        ):
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/winuser/nc-winuser-{callback_lower}"
        elif "completion" in callback_lower or "io" in callback_lower:
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/winbase/nc-winbase-{callback_lower}"
        else:
            # Fallback
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/winuser/nc-winuser-{callback_lower}"

    @classmethod
    def generate_interface_url(
        cls, interface_name: str, locale: str = "en-us"
    ) -> Optional[str]:
        """Gera URL para interfaces COM (nn- prefix)"""
        interface_lower = interface_name.lower()

        # A maioria das interfaces COM está em objbase ou headers específicos
        if interface_name.startswith("I") and len(interface_name) > 1:
            return f"https://learn.microsoft.com/{locale}/windows/win32/api/objbase/nn-objbase-{interface_lower}"

        return None

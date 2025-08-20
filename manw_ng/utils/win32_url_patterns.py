"""
Win32 API URL Pattern Discovery System
====================================

Baseado na pesquisa extensa de padrões de URL do Microsoft Learn.
Implementa heurística robusta para nunca mais falhar na busca de documentação.
"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin


class Win32URLPatterns:
    """Sistema de descoberta de URLs baseado em padrões do Microsoft Learn"""
    
    # Mapeamento header -> módulo baseado na análise
    HEADER_TO_MODULE = {
        # File I/O APIs
        'fileapi.h': 'fileapi',
        'winbase.h': 'winbase',
        
        # Memory APIs
        'memoryapi.h': 'memoryapi',
        'heapapi.h': 'heapapi',
        
        # Process/Thread APIs
        'processthreadsapi.h': 'processthreadsapi',
        
        # Window/User APIs
        'winuser.h': 'winuser',
        
        # Graphics/GDI APIs
        'wingdi.h': 'wingdi',
        
        # Registry APIs
        'winreg.h': 'winreg',
        
        # Network APIs
        'winsock.h': 'winsock',
        'winsock2.h': 'winsock2',
        'ws2tcpip.h': 'winsock2',
        'wininet.h': 'wininet',
        
        # Library loading APIs
        'libloaderapi.h': 'libloaderapi',
        
        # System APIs
        'sysinfoapi.h': 'sysinfoapi',
        'errhandlingapi.h': 'errhandlingapi',
        'securitybaseapi.h': 'securitybaseapi',
        'handleapi.h': 'handleapi',
        'debugapi.h': 'debugapi',
        'profileapi.h': 'profileapi',
        'timeapi.h': 'timeapi',
        'synchapi.h': 'synchapi',
        
        # Console APIs
        'consoleapi.h': 'consoleapi',
        'consoleapi2.h': 'consoleapi2',
        'consoleapi3.h': 'consoleapi3',
        
        # Comm/Device APIs
        'fileapi.h': 'fileapi',
        'commapi.h': 'winbase',  # Often grouped under winbase
        
        # Crypto APIs
        'wincrypt.h': 'wincrypt',
        
        # Service APIs
        'winsvc.h': 'winsvc',
        
        # Shell APIs
        'shellapi.h': 'shellapi',
        'shlobj.h': 'shlobj_core',
        
        # COM APIs
        'objbase.h': 'objbase',
        'combaseapi.h': 'combaseapi',
        
        # RTL/NT APIs
        'winternl.h': 'winternl',
        'ntifs.h': 'ntifs',
        'wdm.h': 'wdm',
        'ntddk.h': 'ntddk',
        
        # Version APIs
        'winver.h': 'winver',
        
        # DLL APIs
        'psapi.h': 'psapi',
        'tlhelp32.h': 'tlhelp32',
        
        # Security APIs
        'aclapi.h': 'aclapi',
        'authz.h': 'authz',
        'lmaccess.h': 'lmaccess',
        
        # Power APIs
        'powrprof.h': 'powrprof',
        'winnt.h': 'winnt',
    }
    
    # Mapeamento function -> module conhecido (casos especiais)
    FUNCTION_TO_MODULE = {
        # File operations
        'createfilea': 'fileapi',
        'createfilew': 'fileapi',
        'readfile': 'fileapi',
        'writefile': 'fileapi',
        'createdirectorya': 'fileapi',
        'createdirectoryw': 'fileapi',
        'deletefilea': 'fileapi',
        'deletefilew': 'fileapi',
        
        # Memory operations
        'virtualalloc': 'memoryapi',
        'virtualallocex': 'memoryapi',
        'virtualfree': 'memoryapi',
        'readprocessmemory': 'memoryapi',
        'writeprocessmemory': 'memoryapi',
        'heapalloc': 'heapapi',
        'heapfree': 'heapapi',
        'heapcreate': 'heapapi',
        
        # Process/Thread operations
        'openprocess': 'processthreadsapi',
        'createprocessa': 'processthreadsapi',
        'createprocessw': 'processthreadsapi',
        'createthread': 'processthreadsapi',
        'createremotethread': 'processthreadsapi',
        'terminateprocess': 'processthreadsapi',
        'terminatethread': 'processthreadsapi',
        'suspendthread': 'processthreadsapi',
        'resumethread': 'processthreadsapi',
        'getprocessid': 'processthreadsapi',
        'getthreadid': 'processthreadsapi',
        'getcurrentprocess': 'processthreadsapi',
        'getcurrentthread': 'processthreadsapi',
        
        # Window operations
        'messageboxa': 'winuser',
        'messageboxw': 'winuser',
        'createwindowa': 'winuser',
        'createwindoww': 'winuser',
        'createwindowexa': 'winuser',
        'createwindowexw': 'winuser',
        'setwindowshookexa': 'winuser',
        'setwindowshookexw': 'winuser',
        'sendmessage': 'winuser',
        'sendmessagea': 'winuser',
        'sendmessagew': 'winuser',
        'postmessage': 'winuser',
        'postmessagea': 'winuser',
        'postmessagew': 'winuser',
        'findwindowa': 'winuser',
        'findwindoww': 'winuser',
        'showwindow': 'winuser',
        'setwindowtext': 'winuser',
        'getwindowtext': 'winuser',
        
        # Registry operations
        'regopenkeyexa': 'winreg',
        'regopenkeyexw': 'winreg',
        'regsetvalueexa': 'winreg',
        'regsetvalueexw': 'winreg',
        'regcreatekeyexa': 'winreg',
        'regcreatekeyexw': 'winreg',
        'regqueryvalueexa': 'winreg',
        'regqueryvalueexw': 'winreg',
        'regclosekey': 'winreg',
        'regdeletekey': 'winreg',
        'regdeletevalue': 'winreg',
        
        # Network operations
        'socket': 'winsock2',
        'connect': 'winsock2',
        'bind': 'winsock2',
        'listen': 'winsock2',
        'accept': 'winsock2',
        'send': 'winsock2',
        'recv': 'winsock2',
        'closesocket': 'winsock2',
        'wsastartup': 'winsock',
        'wsacleanup': 'winsock',
        
        # Library loading
        'loadlibrarya': 'libloaderapi',
        'loadlibraryw': 'libloaderapi',
        'loadlibraryexa': 'libloaderapi',
        'loadlibraryexw': 'libloaderapi',
        'getprocaddress': 'libloaderapi',
        'freelibrary': 'libloaderapi',
        'getmodulehandlea': 'libloaderapi',
        'getmodulehandlew': 'libloaderapi',
        
        # Graphics/GDI
        'bitblt': 'wingdi',
        'createcompatibledc': 'wingdi',
        'createbitmap': 'wingdi',
        'deletedc': 'wingdi',
        'deleteobject': 'wingdi',
        'selectobject': 'wingdi',
        
        # Legacy operations
        'winexec': 'winbase',
        'copyfile': 'winbase',
        'movefile': 'winbase',
        'getmodulefilename': 'winbase',
        'gettemppath': 'winbase',
        'getcomputername': 'winbase',
        
        # RTL functions
        'rtlallocateheap': 'ntifs',
        'rtlfreeheap': 'ntifs',
        'rtlcreateheap': 'ntifs',
        'rtldestroyheap': 'ntifs',
        'rtlcopymemory': 'winternl',
        'rtlzeromemory': 'winternl',
        'rtlmovememory': 'winternl',
    }
    
    # Prefixos de função que indicam o módulo
    MODULE_PREFIXES = {
        'rtl': ['ntifs', 'winternl'],
        'nt': ['winternl', 'ntifs'],
        'zw': ['winternl'],
        'wsa': ['winsock', 'winsock2'],
        'reg': ['winreg'],
        'heap': ['heapapi'],
        'virtual': ['memoryapi'],
        'create': ['processthreadsapi', 'winuser', 'fileapi', 'winbase'],
        'open': ['processthreadsapi', 'fileapi', 'winreg'],
        'read': ['fileapi', 'memoryapi'],
        'write': ['fileapi', 'memoryapi'],
        'get': ['winuser', 'libloaderapi', 'winbase', 'sysinfoapi'],
        'set': ['winuser', 'winreg', 'winbase'],
        'find': ['winuser', 'fileapi'],
        'load': ['libloaderapi'],
        'free': ['libloaderapi', 'heapapi', 'memoryapi'],
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
    def generate_hardware_drivers_url(cls, function_name: str, locale: str = "en-us") -> str:
        """
        Gera URL para funções de drivers de hardware (RTL/NT)
        
        Formato: https://learn.microsoft.com/{locale}/windows-hardware/drivers/ddi/{module}/nf-{module}-{function}
        """
        function_lower = function_name.lower()
        
        # RTL functions geralmente estão em ntifs
        if function_lower.startswith('rtl'):
            module = 'ntifs'
        elif function_lower.startswith('nt') or function_lower.startswith('zw'):
            module = 'winternl'
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
        if any(keyword in function_lower for keyword in ['process', 'thread']):
            return 'processthreadsapi'
        elif any(keyword in function_lower for keyword in ['file', 'directory', 'folder']):
            return 'fileapi'
        elif any(keyword in function_lower for keyword in ['memory', 'virtual', 'heap']):
            return 'memoryapi' if 'virtual' in function_lower else 'heapapi'
        elif any(keyword in function_lower for keyword in ['window', 'message', 'hook']):
            return 'winuser'
        elif any(keyword in function_lower for keyword in ['registry', 'reg', 'key']):
            return 'winreg'
        elif any(keyword in function_lower for keyword in ['socket', 'wsa', 'network']):
            return 'winsock2'
        elif any(keyword in function_lower for keyword in ['library', 'module', 'proc']):
            return 'libloaderapi'
        
        return None
    
    @classmethod
    def get_all_possible_urls(cls, function_name: str, locale: str = "en-us") -> List[str]:
        """
        Gera todas as URLs possíveis para uma função
        """
        urls = []
        
        # URL padrão Win32
        standard_url = cls.generate_url(function_name, locale)
        if standard_url:
            urls.append(standard_url)
        
        # URL para drivers de hardware (RTL/NT)
        hardware_url = cls.generate_hardware_drivers_url(function_name, locale)
        if hardware_url:
            urls.append(hardware_url)
        
        # Variações A/W se a função não tiver sufixo
        function_lower = function_name.lower()
        if not function_lower.endswith('a') and not function_lower.endswith('w'):
            # Tentar versão A
            url_a = cls.generate_url(function_name + 'A', locale)
            if url_a:
                urls.append(url_a)
            
            # Tentar versão W
            url_w = cls.generate_url(function_name + 'W', locale)
            if url_w:
                urls.append(url_w)
        
        # Tentar com módulos alternativos baseado em prefixos
        guessed_module = cls.guess_module(function_name)
        if guessed_module:
            prefix = function_lower[:3]
            if prefix in cls.MODULE_PREFIXES:
                for alt_module in cls.MODULE_PREFIXES[prefix][1:]:  # Pular o primeiro (já tentado)
                    alt_url = f"https://learn.microsoft.com/{locale}/windows/win32/api/{alt_module}/nf-{alt_module}-{function_lower}"
                    urls.append(alt_url)
        
        return list(set(urls))  # Remove duplicatas
    
    @classmethod
    def get_common_modules(cls) -> List[str]:
        """
        Retorna lista de módulos mais comuns para tentativas brutas
        """
        return [
            'processthreadsapi', 'fileapi', 'memoryapi', 'heapapi', 'winuser',
            'winreg', 'winsock2', 'winsock', 'libloaderapi', 'winbase',
            'wingdi', 'sysinfoapi', 'errhandlingapi', 'securitybaseapi',
            'handleapi', 'debugapi', 'profileapi', 'timeapi', 'synchapi',
            'consoleapi', 'shellapi', 'wincrypt', 'winsvc', 'ntifs', 'winternl'
        ]
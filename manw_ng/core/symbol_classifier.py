"""
Classificador profissional de símbolos Win32/Native API
=========================================================

Sistema de taxonomia profissional que distingue tipos de símbolos
vs superfícies de documentação baseado na estrutura real do Microsoft Learn.
"""

import re
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class SymbolInfo:
    """Informações classificadas de um símbolo"""

    symbol: str
    kind: str  # function, struct, enum, callback, interface, macro, etc.
    surface: str  # win32, native-winternl, ddi, printdocs
    header: str
    dll: Optional[str]
    library: Optional[str]
    api_set: Optional[str]
    url_pattern: str  # nf-, ns-, ne-, nc-, nn-
    confidence: float  # 0.0-1.0


class Win32SymbolClassifier:
    """
    Classificador profissional de símbolos Win32/Native baseado em:
    1. Padrões de URL do Microsoft Learn
    2. Prefixos e sufixos de naming conventions
    3. Headers e superfícies de documentação
    """

    # Tipos de símbolos com seus prefixos de URL no Microsoft Learn
    SYMBOL_TYPES = {
        "function": {
            "url_prefix": "nf-",
            "description": "Função Win32/Native API",
            "patterns": [
                r"^(Create|Open|Close|Get|Set|Query|Enum|Find|Register|Unregister)\w+[AW]?$",
                r"^(Nt|Zw|Rtl|Ldr)\w+$",  # Native API
                r"^\w+Ex[AW]?$",  # Extended versions
            ],
        },
        "struct": {
            "url_prefix": "ns-",
            "description": "Estrutura/Typedef",
            "patterns": [
                r"^[A-Z][A-Z_]+$",  # ALL_CAPS structures
                r"^(PEB|TEB|KUSER_SHARED_DATA)$",  # Known structures
                r"^\w+_INFO(CLASS|W|A)?$",  # Info structures
                r"^(STARTUPINFO|PROCESS_INFORMATION|SECURITY_ATTRIBUTES)\w*$",
            ],
        },
        "enum": {
            "url_prefix": "ne-",
            "description": "Enumeração",
            "patterns": [
                r"^\w+CLASS$",  # Info classes
                r"^(TOKEN|SYSTEM|PROCESS|THREAD|FILE)_\w+$",
                r"^(SE_|SECURITY_)\w+$",
            ],
        },
        "callback": {
            "url_prefix": "nc-",
            "description": "Função de Callback",
            "patterns": [
                r"^(LP)?\w+PROC$",  # Window procedures, etc
                r"^(LP)?\w+ROUTINE$",  # Completion routines
                r"^(LP)?\w+CALLBACK$",
            ],
        },
        "interface": {
            "url_prefix": "nn-",
            "description": "Interface COM",
            "patterns": [
                r"^I[A-Z]\w+$",  # COM interfaces start with I
            ],
        },
        "macro": {
            "url_prefix": "",  # Macros often documented inline
            "description": "Macro",
            "patterns": [
                r"^MAKEINTRESOURCE[AW]?$",
                r"^(LOWORD|HIWORD|LOBYTE|HIBYTE)$",
                r"^IS_\w+$",
            ],
        },
        "constant": {
            "url_prefix": "",
            "description": "Constante/Flag",
            "patterns": [
                r"^[A-Z][A-Z0-9_]*$",  # Constants are usually ALL_CAPS
            ],
        },
        "message": {
            "url_prefix": "",
            "description": "Mensagem de Janela",
            "patterns": [
                r"^WM_\w+$",  # Window messages
                r"^(NM|TCN|TVN|LVN)_\w+$",  # Control notifications
            ],
        },
    }

    # Superfícies de documentação com suas características
    SURFACES = {
        "win32": {
            "base_path": "/windows/win32/api",
            "description": "Win32 API Pública",
            "dll_mapping": {
                "winuser": "user32.dll",
                "fileapi": "kernel32.dll",
                "processthreadsapi": "kernel32.dll",
                "winbase": "kernel32.dll",
                "memoryapi": "kernel32.dll",
                "handleapi": "kernel32.dll",
            },
        },
        "native-winternl": {
            "base_path": "/windows/win32/api/winternl",
            "description": "Native API (winternl.h)",
            "dll_mapping": {"winternl": "ntdll.dll"},
        },
        "ddi": {
            "base_path": "/windows-hardware/drivers/ddi",
            "description": "Driver Development Interface",
            "dll_mapping": {
                "ntifs": "ntoskrnl.exe",
                "wdm": "ntoskrnl.exe",
                "ntddk": "ntoskrnl.exe",
            },
        },
        "printdocs": {
            "base_path": "/windows/win32/printdocs",
            "description": "Print Spooler API",
            "dll_mapping": {"": "spoolsv.exe"},
        },
    }

    def classify_symbol(
        self, symbol_name: str, url: Optional[str] = None
    ) -> SymbolInfo:
        """
        Classifica um símbolo baseado no nome e opcionalmente na URL
        """
        symbol = symbol_name.strip()

        # Se temos URL, usar ela para classificação precisa
        if url:
            return self._classify_from_url(symbol, url)

        # Senão, usar heurísticas baseadas no nome
        return self._classify_from_name(symbol)

    def _classify_from_url(self, symbol: str, url: str) -> SymbolInfo:
        """Classificação precisa baseada na URL do Microsoft Learn"""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        # Extrair informações da URL
        surface = self._detect_surface_from_path(path_parts)
        header = self._extract_header_from_path(path_parts)
        url_pattern = self._extract_url_pattern_from_path(path_parts)
        kind = self._kind_from_url_pattern(url_pattern)

        # Determinar DLL baseada na superfície e header
        dll = self._determine_dll(surface, header)

        return SymbolInfo(
            symbol=symbol,
            kind=kind,
            surface=surface,
            header=header,
            dll=dll,
            library=None,  # Pode ser expandido depois
            api_set=None,  # Pode ser expandido depois
            url_pattern=url_pattern,
            confidence=0.95,  # Alta confiança quando temos URL
        )

    def _classify_from_name(self, symbol: str) -> SymbolInfo:
        """Classificação por heurísticas baseadas no nome"""
        best_match = None
        best_confidence = 0.0

        # Testar padrões para cada tipo de símbolo
        for kind, type_info in self.SYMBOL_TYPES.items():
            confidence = self._calculate_pattern_confidence(
                symbol, type_info["patterns"]
            )

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = kind

        # Determinar superfície provável baseada no símbolo
        surface = self._guess_surface_from_symbol(symbol)
        header = self._guess_header_from_symbol(symbol, surface)
        dll = self._determine_dll(surface, header)

        return SymbolInfo(
            symbol=symbol,
            kind=best_match or "unknown",
            surface=surface,
            header=header,
            dll=dll,
            library=None,
            api_set=None,
            url_pattern=self.SYMBOL_TYPES.get(best_match, {}).get("url_prefix", ""),
            confidence=best_confidence,
        )

    def _detect_surface_from_path(self, path_parts: List[str]) -> str:
        """Detecta a superfície baseada no path da URL"""
        path_str = "/".join(path_parts)

        if "windows-hardware/drivers/ddi" in path_str:
            return "ddi"
        elif "windows/win32/printdocs" in path_str:
            return "printdocs"
        elif "winternl" in path_str:
            return "native-winternl"
        elif "windows/win32/api" in path_str:
            return "win32"
        else:
            return "unknown"

    def _extract_header_from_path(self, path_parts: List[str]) -> str:
        """Extrai o header baseado no path"""
        # Padrão típico: /windows/win32/api/{header}/nf-{header}-{function}
        for i, part in enumerate(path_parts):
            if part == "api" and i + 1 < len(path_parts):
                return path_parts[i + 1]
            elif part == "ddi" and i + 1 < len(path_parts):
                return path_parts[i + 1]
        return "unknown"

    def _extract_url_pattern_from_path(self, path_parts: List[str]) -> str:
        """Extrai o padrão de URL (nf-, ns-, etc.)"""
        for part in path_parts:
            if "-" in part:
                prefix = part.split("-")[0] + "-"
                if prefix in ["nf-", "ns-", "ne-", "nc-", "nn-"]:
                    return prefix
        return ""

    def _kind_from_url_pattern(self, url_pattern: str) -> str:
        """Converte padrão de URL para tipo de símbolo"""
        pattern_to_kind = {
            "nf-": "function",
            "ns-": "struct",
            "ne-": "enum",
            "nc-": "callback",
            "nn-": "interface",
        }
        return pattern_to_kind.get(url_pattern, "unknown")

    def _calculate_pattern_confidence(self, symbol: str, patterns: List[str]) -> float:
        """Calcula confiança baseada em padrões regex"""
        if not patterns:
            return 0.0

        for pattern in patterns:
            if re.match(pattern, symbol, re.IGNORECASE):
                return 0.8  # Alta confiança para match exato

        return 0.0

    def _guess_surface_from_symbol(self, symbol: str) -> str:
        """Adivinha a superfície baseada no símbolo"""
        symbol_lower = symbol.lower()

        # Native API patterns
        if symbol.startswith(("Nt", "Zw", "Rtl", "Ldr")) or symbol.upper() in [
            "PEB",
            "TEB",
            "KUSER_SHARED_DATA",
        ]:
            return "native-winternl"

        # Driver/Kernel patterns
        if (
            symbol.startswith(("Io", "Ke", "Mm", "Ob", "Ps"))
            or "_INFORMATION_CLASS" in symbol.upper()
        ):
            return "ddi"

        # Default to Win32
        return "win32"

    def _guess_header_from_symbol(self, symbol: str, surface: str) -> str:
        """Adivinha o header baseado no símbolo e superfície"""
        symbol_lower = symbol.lower()

        if surface == "native-winternl":
            return "winternl"
        elif surface == "ddi":
            if symbol.startswith(("Rtl", "Nt", "Zw")):
                return "ntifs"
            else:
                return "wdm"
        else:
            # Win32 - guess based on function patterns
            if any(x in symbol_lower for x in ["message", "window", "dialog"]):
                return "winuser"
            elif any(x in symbol_lower for x in ["file", "directory", "createfile"]):
                return "fileapi"
            elif any(x in symbol_lower for x in ["process", "thread"]):
                return "processthreadsapi"
            else:
                return "winbase"  # Generic fallback

    def _determine_dll(self, surface: str, header: str) -> Optional[str]:
        """Determina a DLL baseada na superfície e header"""
        surface_info = self.SURFACES.get(surface, {})
        dll_mapping = surface_info.get("dll_mapping", {})

        return dll_mapping.get(header, dll_mapping.get("", None))

    def get_display_info(
        self, symbol_info: SymbolInfo, language: str = "br"
    ) -> Dict[str, str]:
        """Retorna informações para display formatado"""
        kind_translations = {
            "br": {
                "function": "Função",
                "struct": "Estrutura",
                "enum": "Enumeração",
                "callback": "Função de Callback",
                "interface": "Interface COM",
                "macro": "Macro",
                "constant": "Constante",
                "message": "Mensagem de Janela",
                "unknown": "Desconhecido",
            },
            "us": {
                "function": "Function",
                "struct": "Structure",
                "enum": "Enumeration",
                "callback": "Callback Function",
                "interface": "COM Interface",
                "macro": "Macro",
                "constant": "Constant",
                "message": "Window Message",
                "unknown": "Unknown",
            },
        }

        surface_translations = {
            "br": {
                "win32": "Win32 API",
                "native-winternl": "API Nativa (winternl.h)",
                "ddi": "Interface de Driver (DDI)",
                "printdocs": "API de Impressão",
            },
            "us": {
                "win32": "Win32 API",
                "native-winternl": "Native API (winternl.h)",
                "ddi": "Driver Development Interface (DDI)",
                "printdocs": "Print Spooler API",
            },
        }

        lang = language if language in kind_translations else "us"
        kind_name = kind_translations[lang].get(symbol_info.kind, symbol_info.kind)
        surface_name = surface_translations[lang].get(
            symbol_info.surface, symbol_info.surface
        )

        return {
            "type_display": f"{kind_name} {surface_name}",
            "kind": kind_name,
            "surface": surface_name,
            "header_display": f"{symbol_info.header}.h",
            "dll": symbol_info.dll or "N/A",
        }

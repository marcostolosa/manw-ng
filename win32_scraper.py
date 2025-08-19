#!/usr/bin/env python3
"""
Win32 API Documentation Scraper

A revolutionary tool for reverse engineers and Windows developers to extract
detailed information about Win32 API functions from Microsoft documentation.

Supports both English and Portuguese documentation with precise parameter
descriptions, function signatures, and return values.

Author: Marcos
License: MIT
"""

import argparse
import re
import sys
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class Win32APIScraper:
    def __init__(self, language="us", quiet=False):
        self.language = language
        self.quiet = quiet
        if language == "br":
            self.base_url = "https://learn.microsoft.com/pt-br"
            self.search_url_base = (
                "https://learn.microsoft.com/pt-br/search/?scope=Windows&terms="
            )
        else:  # Default to 'us'
            self.base_url = "https://learn.microsoft.com/en-us"
            self.search_url_base = (
                "https://learn.microsoft.com/en-us/search/?scope=Windows&terms="
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def scrape_function(self, function_name: str) -> Dict:
        """
        Faz scraping das informações de uma função Win32 API usando busca dinâmica
        """
        if not self.quiet:
            console.print(f"[cyan]Buscando documentação para: {function_name}[/cyan]")

        # Primeiro tenta URLs conhecidos
        direct_url = self._try_direct_url(function_name)
        if direct_url:
            if not self.quiet:
                console.print(f"[green]Usando URL direto: {direct_url}[/green]")
            return self._parse_function_page(direct_url)

        # Se não encontrou URL direto, usar busca dinâmica
        search_results = self._search_function(function_name)

        # Tenta cada URL encontrada até conseguir fazer o parse com sucesso
        all_urls = search_results if search_results else []

        for url in all_urls:
            try:
                if not self.quiet:
                    console.print(f"[green]Tentando URL: {url}[/green]")
                return self._parse_function_page(url)
            except Exception as e:
                if not self.quiet:
                    console.print(f"[yellow]Falha em {url}: {e}[/yellow]")
                continue

        raise Exception(
            f"Função {function_name} não encontrada na documentação Microsoft"
        )

    def _try_direct_url(self, function_name: str) -> Optional[str]:
        """
        Tenta construir URL direto para funções conhecidas
        """
        # Mapeamento de funções conhecidas para suas URLs
        known_functions = {
            "createprocessw": "processthreadsapi/nf-processthreadsapi-createprocessw",
            "createprocess": "processthreadsapi/nf-processthreadsapi-createprocessw",
            "createfilea": "fileapi/nf-fileapi-createfilea",
            "createfilew": "fileapi/nf-fileapi-createfilew",
            "createfile": "fileapi/nf-fileapi-createfilea",
            "messagebox": "winuser/nf-winuser-messagebox",
            "messageboxw": "winuser/nf-winuser-messageboxw",
            "messageboxa": "winuser/nf-winuser-messageboxa",
            "readfile": "fileapi/nf-fileapi-readfile",
            "writefile": "fileapi/nf-fileapi-writefile",
            "closehandle": "handleapi/nf-handleapi-closehandle",
            "getlasterror": "errhandlingapi/nf-errhandlingapi-getlasterror",
            "virtualalloc": "memoryapi/nf-memoryapi-virtualalloc",
            "virtualfree": "memoryapi/nf-memoryapi-virtualfree",
            "heapalloc": "heapapi/nf-heapapi-heapalloc",
            "heapfree": "heapapi/nf-heapapi-heapfree",
            "heapcreate": "heapapi/nf-heapapi-heapcreate",
            "heapdestroy": "heapapi/nf-heapapi-heapdestroy",
            "getprocessheap": "heapapi/nf-heapapi-getprocessheap",
            "getsysteminfo": "sysinfoapi/nf-sysinfoapi-getsysteminfo",
            "getcurrentprocess": "processthreadsapi/nf-processthreadsapi-getcurrentprocess",
            "getcurrentthread": "processthreadsapi/nf-processthreadsapi-getcurrentthread",
            "loadlibrary": "libloaderapi/nf-libloaderapi-loadlibrarya",
            "loadlibrarya": "libloaderapi/nf-libloaderapi-loadlibrarya",
            "loadlibraryw": "libloaderapi/nf-libloaderapi-loadlibraryw",
            "getprocaddress": "libloaderapi/nf-libloaderapi-getprocaddress",
            "freelibrary": "libloaderapi/nf-libloaderapi-freelibrary",
            "findwindow": "winuser/nf-winuser-findwindowa",
            "findwindowa": "winuser/nf-winuser-findwindowa",
            "findwindoww": "winuser/nf-winuser-findwindoww",
            "setwindowtext": "winuser/nf-winuser-setwindowtexta",
            "getwindowtext": "winuser/nf-winuser-getwindowtexta",
            "showwindow": "winuser/nf-winuser-showwindow",
            "getsystemmetrics": "winuser/nf-winuser-getsystemmetrics",
            "shgetfolderpath": "shlobj_core/nf-shlobj_core-shgetfolderpatha",
            "shgetfolderpatha": "shlobj_core/nf-shlobj_core-shgetfolderpatha",
            "shgetfolderpathw": "shlobj_core/nf-shlobj_core-shgetfolderpathw",
            "openprocess": "processthreadsapi/nf-processthreadsapi-openprocess",
            "terminateprocess": "processthreadsapi/nf-processthreadsapi-terminateprocess",
        }

        func_lower = function_name.lower()
        if func_lower in known_functions:
            return f"{self.base_url}/windows/win32/api/{known_functions[func_lower]}"

        return None

    def _search_function(self, function_name: str) -> List[str]:
        """
        Sistema revolucionário de descoberta automática de URLs para qualquer função Win32
        """
        discovered_urls = []

        # Estratégia 1: Busca inteligente na documentação Microsoft
        discovered_urls.extend(self._search_microsoft_docs(function_name))

        # Estratégia 2: Inferência baseada em padrões de nomenclatura
        discovered_urls.extend(self._infer_urls_from_patterns(function_name))

        # Estratégia 3: Busca no Google especificamente para Microsoft Learn
        discovered_urls.extend(self._search_google_microsoft_learn(function_name))

        # Remove duplicatas mantendo ordem
        seen = set()
        unique_urls = []
        for url in discovered_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        if not self.quiet and unique_urls:
            console.print(
                f"[cyan]Descobrindo URLs: encontradas {len(unique_urls)} possibilidades[/cyan]"
            )

        return unique_urls[:15]  # Retorna até 15 URLs para tentar

    def _search_microsoft_docs(self, function_name: str) -> List[str]:
        """Busca inteligente na documentação Microsoft"""
        results = []

        try:
            # Busca 1: Documentação específica
            search_url = (
                f"{self.search_url_base}{function_name}+win32&category=Documentation"
            )
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Procura por links da documentação Win32 API
            for link in soup.find_all("a", href=True):
                href = link["href"]
                text = link.get_text().lower()

                # Prioriza links que são claramente da documentação da função
                if all(
                    [
                        "/windows/win32/api/" in href.lower(),
                        function_name.lower() in href.lower(),
                        any(
                            keyword in text
                            for keyword in [function_name.lower(), "function", "api"]
                        ),
                    ]
                ):
                    if href.startswith("/"):
                        href = "https://learn.microsoft.com" + href
                    results.append(href)

            # Busca 2: Busca mais ampla se não encontrou nada específico
            if not results:
                broader_search = f"{self.search_url_base}{function_name}+windows+api"
                response2 = self.session.get(broader_search, timeout=10)
                response2.raise_for_status()
                soup2 = BeautifulSoup(response2.content, "html.parser")

                for link in soup2.find_all("a", href=True):
                    href = link["href"]
                    if (
                        "/windows/win32/" in href.lower()
                        and function_name.lower() in href.lower()
                    ):
                        if href.startswith("/"):
                            href = "https://learn.microsoft.com" + href
                        results.append(href)

        except Exception as e:
            if not self.quiet:
                console.print(f"[yellow]Busca Microsoft Docs falhou: {e}[/yellow]")

        return results[:5]

    def _infer_urls_from_patterns(self, function_name: str) -> List[str]:
        """Infere URLs baseado em padrões conhecidos da API Win32"""
        func_lower = function_name.lower()
        inferred_urls = []

        # Análise inteligente do nome da função para determinar categoria
        api_categories = {
            # Padrões de prefixo/sufixo mais específicos
            "heap": ["heapapi"],
            "virtual": ["memoryapi"],
            "memory": ["memoryapi"],
            "global": ["winbase"],
            "local": ["winbase"],
            # File operations
            "file": ["fileapi"],
            "read": ["fileapi"],
            "write": ["fileapi"],
            "create": ["fileapi", "processthreadsapi", "winuser"],
            "delete": ["fileapi"],
            "copy": ["winbase"],
            "move": ["winbase"],
            "find": ["fileapi", "winuser"],
            # Process/Thread
            "process": ["processthreadsapi"],
            "thread": ["processthreadsapi"],
            "terminate": ["processthreadsapi"],
            "suspend": ["processthreadsapi"],
            "resume": ["processthreadsapi"],
            "wait": ["synchapi", "processthreadsapi"],
            # Window/UI
            "window": ["winuser"],
            "message": ["winuser"],
            "dialog": ["winuser", "comdlg32"],
            "menu": ["winuser"],
            "paint": ["wingdi"],
            "draw": ["wingdi"],
            "show": ["winuser"],
            "hide": ["winuser"],
            "get": ["winuser", "fileapi", "processthreadsapi", "winbase"],
            "set": ["winuser", "winreg", "fileapi"],
            # Registry
            "reg": ["winreg"],
            "key": ["winreg"],
            # Library/Module
            "library": ["libloaderapi"],
            "load": ["libloaderapi"],
            "free": ["libloaderapi", "heapapi", "memoryapi"],
            "module": ["libloaderapi"],
            # System
            "system": ["sysinfoapi"],
            "time": ["sysinfoapi"],
            "locale": ["winnls"],
            "version": ["sysinfoapi"],
            # Security
            "token": ["securitybaseapi"],
            "acl": ["securitybaseapi"],
            "security": ["securitybaseapi"],
            # Network
            "wsa": ["winsock", "ws2_32"],
            "socket": ["winsock", "ws2_32"],
            "connect": ["winsock", "ws2_32"],
            "send": ["winsock", "ws2_32"],
            "recv": ["winsock", "ws2_32"],
            "bind": ["winsock", "ws2_32"],
            "listen": ["winsock", "ws2_32"],
            "accept": ["winsock", "ws2_32"],
            # Handle operations
            "handle": ["handleapi"],
            "close": ["handleapi"],
            "duplicate": ["handleapi"],
            # Shell operations
            "sh": ["shlobj_core", "shellapi"],
            "path": ["shlobj_core", "pathapi"],
            "folder": ["shlobj_core"],
            "known": ["shlobj_core"],
        }

        # Encontra todas as categorias relevantes
        relevant_apis = set()
        for keyword, apis in api_categories.items():
            if keyword in func_lower:
                relevant_apis.update(apis)

        # Se não encontrou padrões específicos, usa categorias mais comuns
        if not relevant_apis:
            relevant_apis = [
                "winuser",
                "fileapi",
                "processthreadsapi",
                "memoryapi",
                "winbase",
                "handleapi",
                "shlobj_core",
                "shellapi",
            ]

        # Gera URLs para cada API relevante
        for api in relevant_apis:
            # Formato padrão Microsoft: /windows/win32/api/{api}/nf-{api}-{function}
            base_url = f"{self.base_url}/windows/win32/api/{api}/nf-{api}-{func_lower}"
            inferred_urls.append(base_url)

            # Tenta variações A/W se a função não termina com A ou W
            if not func_lower.endswith("a") and not func_lower.endswith("w"):
                inferred_urls.append(f"{base_url}a")
                inferred_urls.append(f"{base_url}w")

        return inferred_urls[:10]

    def _search_google_microsoft_learn(self, function_name: str) -> List[str]:
        """Busca no Google especificamente por páginas do Microsoft Learn"""
        # Por limitações de implementação, simula uma busca inteligente
        # Em um ambiente de produção, usaria a API do Google Search

        potential_urls = []

        # Gera URLs baseadas em padrões comuns que o Google encontraria
        common_apis = [
            "winuser",
            "fileapi",
            "processthreadsapi",
            "memoryapi",
            "winbase",
            "handleapi",
            "errhandlingapi",
            "sysinfoapi",
            "libloaderapi",
            "heapapi",
            "securitybaseapi",
            "winreg",
            "synchapi",
            "wingdi",
            "winsock",
            "ws2_32",
            "shlobj_core",
            "shellapi",
            "pathapi",
        ]

        func_lower = function_name.lower()
        for api in common_apis:
            url = f"{self.base_url}/windows/win32/api/{api}/nf-{api}-{func_lower}"
            potential_urls.append(url)

        return potential_urls[:5]

    def _generate_fallback_urls(self, function_name: str) -> List[str]:
        """
        Gera URLs de fallback inteligentes baseadas em padrões comuns da API Win32
        """
        func_lower = function_name.lower()
        fallback_urls = []

        # Padrões de API mais comuns organizados por categorias
        api_patterns = {
            # Memory APIs
            "heap": ["heapapi"],
            "virtual": ["memoryapi"],
            "memory": ["memoryapi"],
            "global": ["winbase"],
            "local": ["winbase"],
            # File APIs
            "file": ["fileapi"],
            "read": ["fileapi"],
            "write": ["fileapi"],
            "create": ["fileapi", "processthreadsapi"],
            "delete": ["fileapi"],
            "copy": ["winbase"],
            "move": ["winbase"],
            # Process/Thread APIs
            "process": ["processthreadsapi"],
            "thread": ["processthreadsapi"],
            "terminate": ["processthreadsapi"],
            "suspend": ["processthreadsapi"],
            "resume": ["processthreadsapi"],
            # Window APIs
            "window": ["winuser"],
            "message": ["winuser"],
            "dialog": ["winuser"],
            "menu": ["winuser"],
            "paint": ["wingdi"],
            "draw": ["wingdi"],
            # Registry APIs
            "reg": ["winreg"],
            "key": ["winreg"],
            # Error handling
            "error": ["errhandlingapi"],
            "exception": ["errhandlingapi"],
            # Library APIs
            "library": ["libloaderapi"],
            "load": ["libloaderapi"],
            "get": ["libloaderapi", "winuser", "fileapi", "processthreadsapi"],
            "set": ["winuser", "winreg", "fileapi"],
            # System APIs
            "system": ["sysinfoapi"],
            "time": ["sysinfoapi"],
            "locale": ["winnls"],
        }

        # Encontra APIs relevantes baseadas no nome da função
        relevant_apis = set()
        for keyword, apis in api_patterns.items():
            if keyword in func_lower:
                relevant_apis.update(apis)

        # Se não encontrou padrões específicos, usa APIs mais comuns
        if not relevant_apis:
            relevant_apis = [
                "winuser",
                "fileapi",
                "processthreadsapi",
                "memoryapi",
                "winbase",
            ]

        # Gera URLs de fallback para cada API relevante
        for api in relevant_apis:
            # Formato padrão: /windows/win32/api/{api}/nf-{api}-{function}
            fallback_url = (
                f"{self.base_url}/windows/win32/api/{api}/nf-{api}-{func_lower}"
            )
            fallback_urls.append(fallback_url)

            # Também tenta variações comuns (A/W)
            if not func_lower.endswith("a") and not func_lower.endswith("w"):
                fallback_urls.append(
                    f"{self.base_url}/windows/win32/api/{api}/nf-{api}-{func_lower}a"
                )
                fallback_urls.append(
                    f"{self.base_url}/windows/win32/api/{api}/nf-{api}-{func_lower}w"
                )

        if not self.quiet:
            console.print(
                f"[cyan]Tentando {len(fallback_urls)} URLs de fallback...[/cyan]"
            )

        return fallback_urls[:10]  # Limita a 10 tentativas

    def _parse_function_page(self, url: str) -> Dict:
        """
        Parseia a página de documentação de uma função específica usando extração dinâmica
        """
        if not self.quiet:
            console.print(f"[blue]Analisando página: {url}[/blue]")

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            raise Exception(f"Erro ao acessar página: {e}")

        function_info = {
            "url": url,
            "name": "",
            "dll": "",
            "calling_convention": "__stdcall",
            "parameters": [],
            "parameter_count": 0,
            "architectures": ["x86", "x64"],
            "signature": "",
            "return_type": "",
            "return_description": "",
            "description": "",
        }

        # Extração dinâmica para qualquer função
        function_info["name"] = self._extract_function_name(soup)
        function_info["dll"] = self._extract_dll(soup)
        function_info["signature"] = self._extract_signature(soup)
        function_info["parameters"] = self._extract_parameters(soup)
        function_info["parameter_count"] = len(function_info["parameters"])
        function_info["return_type"], function_info["return_description"] = (
            self._extract_return_info(soup)
        )
        function_info["architectures"] = self._extract_architectures(soup)
        function_info["description"] = self._extract_description(soup)

        return function_info

    def _extract_function_name(self, soup: BeautifulSoup) -> str:
        """Extrai o nome da função"""
        # Tenta várias estratégias para extrair o nome da função

        # 1. Título principal (h1)
        title = soup.find("h1")
        if title:
            title_text = title.get_text().strip()
            # Remove texto extra como "function" ou "API"
            title_text = re.sub(
                r"\s+(function|api|Function|API).*$",
                "",
                title_text,
                flags=re.IGNORECASE,
            )
            if title_text:
                return title_text

        # 2. Procura no código por assinatura da função
        code_blocks = soup.find_all(["pre", "code"])
        for block in code_blocks:
            text = block.get_text()
            # Procura por padrão de função: TIPO NomeFuncao(
            match = re.search(r"\b(\w+)\s*\(", text)
            if match and not match.group(1).upper() in ["IF", "FOR", "WHILE", "SWITCH"]:
                return match.group(1)

        # 3. Extrai da URL se necessário
        return "FunçãoDesconhecida"

    def _extract_dll(self, soup: BeautifulSoup) -> str:
        """Extrai o nome da DLL"""
        # Procura por texto que menciona .dll
        dll_patterns = [r"(\w+\.dll)", r"Library:\s*(\w+\.dll)", r"DLL:\s*(\w+\.dll)"]

        text = soup.get_text()
        for pattern in dll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return "kernel32.dll"  # Padrão para a maioria das funções Win32

    def _extract_signature(self, soup: BeautifulSoup) -> str:
        """Extrai a assinatura da função da div com class='has-inner-focus'"""
        # Primeiro procura especificamente pela div com class="has-inner-focus"
        focus_div = soup.find("div", class_="has-inner-focus")
        if focus_div:
            signature = focus_div.get_text().strip()
            if signature and "(" in signature and ")" in signature:
                return signature

        # Fallback: procura pela seção "Syntax" ou "Sintaxe"
        syntax_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Syntax|Sintaxe|syntax|sintaxe", re.IGNORECASE),
        )
        for header in syntax_headers:
            # Procura pelo próximo elemento de código após o cabeçalho
            next_elem = header.find_next()
            while next_elem:
                if next_elem.name in ["pre", "code"]:
                    signature = next_elem.get_text().strip()
                    if "(" in signature and ")" in signature:
                        return signature
                elif next_elem.name == "div" and "has-inner-focus" in next_elem.get(
                    "class", []
                ):
                    signature = next_elem.get_text().strip()
                    if "(" in signature and ")" in signature:
                        return signature
                next_elem = next_elem.find_next_sibling()
                # Para não ir muito longe
                if next_elem and next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

        # Fallback final: procura por blocos de código com alta pontuação
        code_blocks = soup.find_all(["pre", "code"])
        best_signature = ""
        max_score = 0

        for block in code_blocks:
            text = block.get_text().strip()

            # Calcula um score baseado em indicadores de assinatura de função
            score = 0
            if "(" in text and ")" in text:
                score += 1
            if any(
                keyword in text.upper()
                for keyword in ["BOOL", "DWORD", "HANDLE", "LP", "VOID", "INT"]
            ):
                score += 2
            if "[in]" in text or "[out]" in text or "[optional]" in text:
                score += 3
            if len(text.split("\n")) > 2:  # Assinatura multi-linha
                score += 1
            if text.count(",") >= 2:  # Múltiplos parâmetros
                score += 1

            # Prefere assinaturas que não sejam apenas estruturas ou definições
            if text.startswith("typedef") or text.startswith("struct"):
                score -= 2

            if score > max_score and len(text) > 10:
                max_score = score
                best_signature = text

        return best_signature

    def _extract_parameters(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrai informações detalhadas dos parâmetros da seção Parameters"""
        parameters = []

        # Estratégia 1: Procura pela seção "Parameters" ou "Parâmetros" - método avançado
        param_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Parameters|Parâmetros|parameters", re.IGNORECASE),
        )

        for header in param_headers:
            # Procura por dt/dd após a seção Parameters
            next_elem = header.find_next_sibling()
            current_param = {}

            while next_elem:
                # Para quando encontra outro cabeçalho
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                if next_elem.name == "dt":
                    # Se já temos um parâmetro sendo processado, salva ele
                    if current_param.get("name"):
                        parameters.append(current_param)

                    param_name = next_elem.get_text().strip()
                    # Remove colchetes de direção se existir
                    param_name = re.sub(r"^\[.*?\]\s*", "", param_name)
                    current_param = {
                        "name": param_name,
                        "type": self._extract_type_from_text(param_name),
                        "description": "",
                    }

                elif next_elem.name == "dd" and current_param.get("name"):
                    # Extrai toda a descrição detalhada
                    description_parts = []

                    # Procura por todos os elementos de texto dentro do dd
                    for elem in next_elem.find_all(string=True):
                        text = elem.strip()
                        if text:
                            description_parts.append(text)

                    # Também pega texto direto do dd
                    direct_text = next_elem.get_text().strip()
                    if direct_text and direct_text not in " ".join(description_parts):
                        description_parts.append(direct_text)

                    current_param["description"] = " ".join(description_parts)

                    # Tenta extrair o tipo mais preciso da descrição
                    desc_text = current_param["description"].upper()
                    for win_type in [
                        "HWND",
                        "HANDLE",
                        "LPCSTR",
                        "LPCWSTR",
                        "LPSTR",
                        "LPWSTR",
                        "DWORD",
                        "UINT",
                        "INT",
                        "BOOL",
                        "LPVOID",
                        "PVOID",
                    ]:
                        if win_type in desc_text:
                            current_param["type"] = win_type
                            break

                next_elem = next_elem.find_next_sibling()

            # Adiciona o último parâmetro se existe
            if current_param.get("name"):
                parameters.append(current_param)

            if parameters:  # Se encontrou parâmetros, para a busca
                break

        # Estratégia 2: Método revolucionário - extração da assinatura + busca das descrições
        if not parameters:
            signature = self._extract_signature(soup)
            if signature and "(" in signature and ")" in signature:
                param_text = signature[signature.find("(") + 1 : signature.rfind(")")]
                param_lines = [
                    line.strip()
                    for line in param_text.split("\n")
                    if line.strip() and not line.strip() == ","
                ]

                # Extrai parâmetros da assinatura
                signature_params = []
                for line in param_lines:
                    # Remove comentários
                    line = re.sub(r"//.*$", "", line)
                    line = re.sub(r"/\*.*?\*/", "", line)
                    line = line.rstrip(",").strip()

                    # Procura por padrão: [direção] TIPO nome
                    match = re.search(r"\[([^\]]+)\]\s*(\w+)\s+(\w+)", line)
                    if match:
                        direction, param_type, param_name = match.groups()
                        signature_params.append(
                            {
                                "name": param_name,
                                "type": param_type,
                                "direction": direction,
                            }
                        )

                # Agora busca as descrições detalhadas para cada parâmetro
                for param in signature_params:
                    description = self._find_parameter_description(soup, param["name"])
                    parameters.append(
                        {
                            "name": param["name"],
                            "type": param["type"],
                            "description": (
                                description
                                if description
                                else f"[{param['direction']}] {param['type']} parameter"
                            ),
                        }
                    )

        # Estratégia 3: Fallback - extração básica da assinatura
        if not parameters:
            signature = self._extract_signature(soup)
            if signature and "(" in signature and ")" in signature:
                param_text = signature[signature.find("(") + 1 : signature.rfind(")")]
                param_lines = [
                    line.strip() for line in param_text.split("\n") if line.strip()
                ]

                for line in param_lines:
                    line = re.sub(r"//.*$", "", line)
                    line = re.sub(r"/\*.*?\*/", "", line)
                    line = line.rstrip(",").strip()

                    match = re.search(r"\[([^\]]+)\]\s*(\w+)\s+(\w+)", line)
                    if match:
                        direction, param_type, param_name = match.groups()
                        parameters.append(
                            {
                                "name": param_name,
                                "type": param_type,
                                "description": f"[{direction}] {param_type} parameter",
                            }
                        )

        return parameters

    def _find_parameter_description(self, soup: BeautifulSoup, param_name: str) -> str:
        """Busca a descrição detalhada de um parâmetro específico na página"""
        # Primeiro, tenta buscar em estruturas dt/dd
        dt_elements = soup.find_all("dt")
        for dt in dt_elements:
            dt_text = dt.get_text().strip()
            # Verifica se este dt contém o nome do parâmetro (pode ter colchetes como [in, optional] lpApplicationName)
            if re.search(r"\b" + re.escape(param_name) + r"\b", dt_text, re.IGNORECASE):
                dd = dt.find_next_sibling("dd")
                if dd:
                    description = dd.get_text().strip()
                    if len(description) > 10:  # Descrição decente
                        return description

        # Estratégia revolucionária: busca na seção Parameters por texto sequencial
        param_sections = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Parameters|Parâmetros|parameters", re.IGNORECASE),
        )

        for header in param_sections:
            # Pega todo o conteúdo da seção Parameters
            content = []
            next_elem = header.find_next_sibling()

            while next_elem:
                if next_elem.name in [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                ]:  # Para em próximo cabeçalho
                    break
                content.append(next_elem.get_text())
                next_elem = next_elem.find_next_sibling()

            # Combina todo o texto da seção
            full_text = " ".join(content)

            # Divide o texto por padrões que indicam início de novo parâmetro
            # Procura por padrões como "[in] lpApplicationName" ou "\nlpApplicationName"
            param_pattern = (
                r"(?:\[(?:in|out|in,\s*out)(?:,\s*optional)?\]\s*)?"
                + re.escape(param_name)
                + r"\b"
            )
            match = re.search(param_pattern, full_text, re.IGNORECASE)

            if match:
                # Pega o texto após o nome do parâmetro
                start_pos = match.end()
                remaining_text = full_text[start_pos:]

                # Procura pelo fim da descrição (próximo parâmetro ou seção)
                # Lista de nomes de parâmetros comuns para detectar onde para
                common_params = [
                    "lpApplicationName",
                    "lpCommandLine",
                    "lpProcessAttributes",
                    "lpThreadAttributes",
                    "bInheritHandles",
                    "dwCreationFlags",
                    "lpEnvironment",
                    "lpCurrentDirectory",
                    "lpStartupInfo",
                    "lpProcessInformation",
                    "hWnd",
                    "lpText",
                    "lpCaption",
                    "uType",
                ]

                # Remove o parâmetro atual da lista
                other_params = [
                    p for p in common_params if p.lower() != param_name.lower()
                ]

                # Procura onde termina a descrição
                end_pos = len(remaining_text)
                for other_param in other_params:
                    pattern = (
                        r"(?:\[(?:in|out|in,\s*out)(?:,\s*optional)?\]\s*)?"
                        + re.escape(other_param)
                        + r"\b"
                    )
                    next_match = re.search(pattern, remaining_text, re.IGNORECASE)
                    if next_match and next_match.start() < end_pos:
                        end_pos = next_match.start()

                # Também procura por seções como "Return value"
                for section in ["Return value", "Remarks", "Requirements", "Examples"]:
                    section_match = re.search(
                        re.escape(section), remaining_text, re.IGNORECASE
                    )
                    if section_match and section_match.start() < end_pos:
                        end_pos = section_match.start()

                description = remaining_text[:end_pos].strip()

                # Limpa a descrição
                description = re.sub(
                    r"^\s*-\s*", "", description
                )  # Remove traços iniciais
                description = re.sub(r"\s+", " ", description)  # Normaliza espaços
                description = description.strip()

                if len(description) > 20:  # Descrição decente
                    return description[:1000]  # Limita tamanho

        return ""

    def _extract_type_from_text(self, text: str) -> str:
        """Extrai o tipo de dados de um texto"""
        # Procura por tipos Win32 comuns
        win32_types = [
            "BOOL",
            "DWORD",
            "HANDLE",
            "HWND",
            "LPCSTR",
            "LPCWSTR",
            "LPSTR",
            "LPWSTR",
            "LPVOID",
            "PVOID",
            "UINT",
            "INT",
            "LONG",
            "ULONG",
            "BYTE",
            "WORD",
        ]

        text_upper = text.upper()
        for win_type in win32_types:
            if win_type in text_upper:
                return win_type

        # Procura por padrões LP*
        lp_match = re.search(r"LP\w+", text_upper)
        if lp_match:
            return lp_match.group(0)

        return "UNKNOWN"

    def _extract_return_info(self, soup: BeautifulSoup) -> Tuple[str, str]:
        """Extrai informações sobre o valor de retorno da seção específica"""
        return_type = "BOOL"  # Padrão comum
        return_desc = ""

        # Primeiro, procura pela seção "Return value" ou "Valor de retorno"
        return_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(
                r"Return\s+value|Valor\s+de\s+retorno|return\s+value|valor\s+retornado|valor\s+retorno|return\s+values",
                re.IGNORECASE,
            ),
        )

        for header in return_headers:
            # Pega todo o conteúdo entre este header e o próximo header
            content_parts = []
            next_elem = header.find_next_sibling()

            paragraph_count = 0
            while (
                next_elem and paragraph_count < 2
            ):  # Limita a 2 parágrafos para ser mais conciso
                # Para quando encontra outro cabeçalho
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                # Coleta texto de parágrafos principais (mais restritivo)
                if next_elem.name in ["p"]:
                    text = next_elem.get_text().strip()
                    if (
                        text and len(text) > 10 and len(text) < 500
                    ):  # Evita textos muito longos
                        content_parts.append(text)
                        paragraph_count += 1
                # Para listas, pega apenas o primeiro item se ainda não tem conteúdo
                elif next_elem.name in ["ul", "ol"] and paragraph_count == 0:
                    first_li = next_elem.find("li")
                    if first_li:
                        text = first_li.get_text().strip()
                        if text and len(text) < 300:
                            content_parts.append(text)
                            paragraph_count += 1

                next_elem = next_elem.find_next_sibling()

            if content_parts:
                return_desc = " ".join(content_parts)
                break

        # Fallback melhorado: procura por seções com palavras-chave específicas de valor de retorno
        if not return_desc:
            # Estratégia 1: Procura por texto que comece com frases típicas de valor de retorno
            all_text_elements = soup.find_all(["p", "div", "li"])
            for elem in all_text_elements:
                text = elem.get_text().strip()
                # Procura por frases que indiquem valor de retorno
                if (
                    any(
                        phrase in text.lower()
                        for phrase in [
                            "if the function succeeds",
                            "if the function fails",
                            "se a função for bem-sucedida",
                            "se a função falhar",
                            "retorna um ponteiro",
                            "returns a pointer",
                            "return value is",
                            "valor retornado é",
                            "valor de retorno é",
                        ]
                    )
                    and 20 <= len(text) <= 400
                ):
                    return_desc = text
                    break

            # Estratégia 2: Se ainda não encontrou, busca por elementos próximos a headers de retorno
            if not return_desc:
                return_elements = soup.find_all(
                    ["p", "div", "dt", "dd"],
                    string=re.compile(r"return|retorno", re.IGNORECASE),
                )

            for elem in return_elements:
                parent = elem.parent if hasattr(elem, "parent") else elem

                # Se é um elemento de definição (dt/dd), pega o dd correspondente
                if parent.name == "dt":
                    dd = parent.find_next_sibling("dd")
                    if dd:
                        return_desc = dd.get_text().strip()
                        break
                elif parent.name in ["p", "div"]:
                    text = parent.get_text().strip()
                    # Procura por texto que pareça ser descrição de retorno
                    if len(text) > 20 and (
                        "succeed" in text.lower()
                        or "fail" in text.lower()
                        or "nonzero" in text.lower()
                        or "zero" in text.lower()
                        or "true" in text.lower()
                        or "false" in text.lower()
                        or "sucesso" in text.lower()
                        or "falha" in text.lower()
                        or "êxito" in text.lower()
                        or "erro" in text.lower()
                        or "retorna" in text.lower()
                        or "ponteiro" in text.lower()
                        or "null" in text.lower()
                    ):
                        return_desc = text
                        break

        # Tenta extrair o tipo de retorno da assinatura
        signature = self._extract_signature(soup)
        if signature:
            # Procura por padrão tipo + nome_funcao( (incluindo tipos compostos como DECLSPEC_ALLOCATOR LPVOID)
            match = re.search(
                r"^\s*(?:\w+\s+)*(\w+)\s+\w+\s*\(", signature, re.MULTILINE
            )
            if match:
                potential_type = match.group(1).upper()
                if potential_type in [
                    "BOOL",
                    "DWORD",
                    "HANDLE",
                    "HWND",
                    "INT",
                    "UINT",
                    "LONG",
                    "ULONG",
                    "VOID",
                    "LPVOID",
                ]:
                    return_type = potential_type

        return return_type, return_desc

    def _extract_architectures(self, soup: BeautifulSoup) -> List[str]:
        """Extrai arquiteturas suportadas"""
        # Procura por informações sobre versões do Windows e arquiteturas
        text = soup.get_text().lower()
        architectures = []

        if "x64" in text or "64-bit" in text:
            architectures.append("x64")
        if "x86" in text or "32-bit" in text or "desktop" in text:
            architectures.append("x86")

        # Se não encontrar, assume ambas
        if not architectures:
            architectures = ["x86", "x64"]

        return architectures

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrai a descrição da função"""
        # Procura pelo primeiro parágrafo após o título
        title = soup.find("h1")
        if title:
            next_p = title.find_next("p")
            if next_p:
                return next_p.get_text().strip()

        return ""

    def format_output(self, function_info: Dict) -> None:
        """
        Formata e exibe as informações extraídas usando Rich
        """
        # Título principal
        console.print(
            Panel(
                f"[bold blue]{function_info['name']}[/bold blue]",
                title="Win32 API Function",
                expand=False,
            )
        )

        # Informações básicas
        basic_table = Table(title="Informações Básicas")
        basic_table.add_column("Propriedade", style="cyan")
        basic_table.add_column("Valor", style="magenta")

        basic_table.add_row("DLL", function_info["dll"])
        basic_table.add_row("Calling Convention", function_info["calling_convention"])
        basic_table.add_row(
            "Número de Parâmetros", str(function_info["parameter_count"])
        )
        basic_table.add_row("Arquiteturas", ", ".join(function_info["architectures"]))
        basic_table.add_row("Tipo de Retorno", function_info["return_type"])

        console.print(basic_table)

        # Assinatura da função
        if function_info["signature"]:
            console.print(
                Panel(
                    Markdown(f"```c\n{function_info['signature']}\n```"),
                    title="Assinatura da Função",
                )
            )

        # Descrição
        if function_info["description"]:
            console.print(Panel(function_info["description"], title="Descrição"))

        # Parâmetros
        if function_info["parameters"]:
            param_table = Table(title="Parâmetros")
            param_table.add_column("Nome", style="cyan")
            param_table.add_column("Descrição", style="green")

            for param in function_info["parameters"]:
                param_table.add_row(
                    param["name"],
                    (
                        param["description"][:100] + "..."
                        if len(param["description"]) > 100
                        else param["description"]
                    ),
                )

            console.print(param_table)

        # Valor de retorno
        if function_info["return_description"]:
            console.print(
                Panel(function_info["return_description"], title="Valor de Retorno")
            )


def main():
    parser = argparse.ArgumentParser(
        description="Scraper para documentação Win32 API da Microsoft"
    )
    parser.add_argument(
        "function_name",
        help="Nome da função Win32 para fazer scraping (ex: CreateProcessW)",
    )
    parser.add_argument(
        "-l",
        "--language",
        choices=["br", "us"],
        default="us",
        help="Idioma da documentação: 'br' para português ou 'us' para inglês (padrão: us)",
    )
    parser.add_argument(
        "--output",
        choices=["rich", "json", "markdown"],
        default="rich",
        help="Formato de saída (padrão: rich)",
    )

    args = parser.parse_args()

    try:
        scraper = Win32APIScraper(language=args.language, quiet=(args.output == "json"))
        if args.output != "json":
            console.print(
                f"[yellow]Fazendo scraping da função: {args.function_name} (idioma: {args.language})[/yellow]"
            )

        function_info = scraper.scrape_function(args.function_name)

        if args.output == "rich":
            scraper.format_output(function_info)
        elif args.output == "json":
            import json

            print(json.dumps(function_info, indent=2, ensure_ascii=False))
        elif args.output == "markdown":
            # Implementar formatação markdown aqui
            pass

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

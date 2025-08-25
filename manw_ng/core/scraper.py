"""
Core Win32 API Scraper for MANW-NG

Main scraper class that orchestrates the discovery and parsing process.
"""

from typing import Dict, Optional, List
import random
import time
import asyncio
from bs4 import BeautifulSoup
from rich.console import Console
from rich.status import Status

from ..core.parser import Win32PageParser
from ..utils.complete_win32_api_mapping import get_function_url_fast
from ..utils.smart_url_generator import SmartURLGenerator
from ..utils.catalog_integration import get_catalog
from ..utils.http_client import HTTPClient


class Win32APIScraper:
    """
    Main Win32 API documentation scraper
    """

    def __init__(
        self,
        language="us",
        quiet: bool = False,
        user_agent: Optional[str] = None,
        proxies: Optional[List[str]] = None,
        rate_limit: int = 5,
        rotate_user_agent: bool = False,
    ):
        self.language = language
        self.quiet = quiet

        if language == "br":
            self.base_url = "https://learn.microsoft.com/pt-br"
        else:
            self.base_url = "https://learn.microsoft.com/en-us"

        if user_agent is None:
            # Use the smart generator's user agent system
            temp_generator = SmartURLGenerator()
            user_agent = temp_generator.user_agents_flat[0]

        # Async HTTP client with intelligent caching and rotation support
        self.http = HTTPClient(
            user_agent=user_agent,
            proxies=proxies,
            rate_limit=rate_limit,
            rotate_user_agent=rotate_user_agent,
            cache_ttl=7200,  # 2 hours cache for Win32 API docs
        )
        self.user_agent = user_agent

        # Initialize modules
        # Initialize smart URL generator
        self.parser = Win32PageParser()
        # Windows-safe console configuration
        self.console = Console(
            force_terminal=True, legacy_windows=True, color_system="truecolor"
        )
        self.smart_generator = SmartURLGenerator()

        # Elegant Unicode characters
        self.check_mark = "✓"
        self.arrow = "→"
        self.catalog = get_catalog()

        # Localized strings
        self.strings = {
            "us": {
                "documentation_found": "Documentation found:",
                "testing": "Testing:",
                "fallback_to_english": "pt-br not found, trying en-us:",
                "searching": "Searching for function documentation...",
                "trying_direct": "Checking direct URL mapping...",
                "discovery_search": "Using intelligent discovery system...",
                "function_not_found": "Function {function_name} not found in Microsoft documentation",
            },
            "br": {
                "documentation_found": "Documentação encontrada:",
                "testing": "Testando:",
                "fallback_to_english": "pt-br não encontrada, tentando en-us:",
                "searching": "Procurando documentação da função...",
                "trying_direct": "Verificando mapeamento direto de URL...",
                "discovery_search": "Usando sistema de descoberta inteligente...",
                "function_not_found": "Função {function_name} não encontrada na documentação Microsoft",
            },
        }

    def set_current_function_dll(self, dll_name: str) -> None:
        """Public setter to define the DLL used for smart URL generation."""
        self._current_function_dll = dll_name

    def get_string(self, key: str) -> str:
        """Get localized string"""
        return self.strings.get(self.language, self.strings["us"]).get(key, key)

    def scrape_function(self, function_name: str) -> Dict:
        """
        Main function to scrape Win32 API documentation
        """

        if not self.quiet:
            # PRIORITY 1: Smart URL Testing with intelligent patterns
            try:
                with Status(
                    f"[cyan]1/3[/cyan] Testando padrões inteligentes para [bold]{function_name}[/bold]...",
                    console=self.console,
                ) as status:
                    # Use the SMART synchronous method with maximum concurrency
                    dll_name = getattr(self, "_current_function_dll", None)

                    def progress(done: int, total: int) -> None:
                        status.update(
                            f"[cyan]1/3[/cyan] Testando URLs ({done}/{total})..."
                        )

                    found_url = asyncio.run(
                        self.smart_generator.find_valid_url_async(
                            function_name,
                            dll_name,
                            self.base_url,
                            progress_callback=progress,
                        )
                    )

                    if found_url:
                        status.update(
                            f"[green]1/3[/green] URL encontrada: [blue]{self._format_url_display(found_url)}[/blue]"
                        )
                        result = self._parse_function_page(found_url)
                        if result and result.get("documentation_found"):
                            status.stop()
                            self.console.print(
                                f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(found_url)}[/green]"
                            )
                            return result

                    status.update(
                        f"[yellow]1/3[/yellow] ULTRA-FAST: Nenhuma URL encontrada nos padrões conhecidos"
                    )
            except Exception as e:
                pass  # Silently continue to next priority
                # import traceback
                # traceback.print_exc()

            # PRIORITY 2: Try catalog lookup (backup)
            with Status(
                f"[cyan]2/3[/cyan] Verificando catálogo para [bold]{function_name}[/bold]...",
                console=self.console,
            ) as status:
                catalog_url = self.catalog.get_function_url(
                    function_name, "en-us" if self.language == "us" else "pt-br"
                )
                if catalog_url:
                    status.update(
                        f"[cyan]2/3[/cyan] Testando URL do catálogo: [blue]{self._format_url_display(catalog_url)}[/blue]"
                    )
                    result = self._parse_function_page(catalog_url)
                    if result:
                        status.stop()
                        self.console.print(
                            f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(catalog_url)}[/green]"
                        )
                        return result
                    status.update(
                        f"[yellow]2/3[/yellow] Catálogo não retornou resultado válido"
                    )

            # PRIORITY 3: Use direct mapping (final backup)
            with Status(
                f"[cyan]3/3[/cyan] Testando mapeamento direto para [bold]{function_name}[/bold]...",
                console=self.console,
            ) as status:
                direct_url = self._try_direct_url(function_name)
                if direct_url:
                    status.update(
                        f"[cyan]3/3[/cyan] Testando URL direto: [blue]{self._format_url_display(direct_url)}[/blue]"
                    )
                    result = self._parse_function_page(direct_url)
                    if result:
                        status.stop()
                        self.console.print(
                            f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(direct_url)}[/green]"
                        )
                        return result
                    status.update(
                        f"[yellow]3/3[/yellow] Mapeamento direto não funcionou"
                    )

            search_results = []  # No discovery engine
        else:
            # Silent mode - use ONLY smart generator for speed
            direct_url = self._try_direct_url(function_name)
            if direct_url:
                result = self._parse_function_page(direct_url)
                if result:
                    return result

            # PRIORITY: ULTRA-FAST Smart generator with ALL patterns
            dll_name = getattr(self, "_current_function_dll", None)
            found_url = asyncio.run(
                self.smart_generator.find_valid_url_async(
                    function_name, dll_name, self.base_url
                )
            )

            if found_url:
                result = self._parse_function_page(found_url)
                if result and result.get("documentation_found"):
                    return result

            # NO DISCOVERY ENGINE FALLBACK - too slow
            search_results = []

        # Try each discovered URL with Rich Status
        if not self.quiet and search_results:
            with Status("", console=self.console) as status:
                for i, url in enumerate(search_results, 1):
                    try:
                        status.update(
                            f"[cyan]•[/cyan] [bold]{function_name}[/bold] [dim]({i}/{len(search_results)})[/dim] {self.arrow} [blue]{self._format_url_display(url)}[/blue]"
                        )
                        result = self._parse_function_page(url, status)

                        if result:  # Se resultado válido
                            status.stop()
                            self.console.print(
                                f"[green]OK[/green] [bold]{function_name}[/bold] -> [green]{self._format_url_display(url)}[/green]"
                            )
                            return result

                    except Exception as e:
                        continue

                status.stop()
        else:
            # Silent mode
            for url in search_results:
                try:
                    result = self._parse_function_page(url)
                    if result:  # Se resultado válido
                        if not self.quiet:
                            self.console.print(
                                f"[green]OK[/green] [bold]{function_name}[/bold] -> [green]{self._format_url_display(url)}[/green]"
                            )
                        return result
                except Exception as e:
                    continue

        # FINAL: Handle A/W suffix variations before giving up
        if not function_name.endswith(("A", "W")):
            if not self.quiet:
                with Status(
                    f"[cyan]FINAL[/cyan] Testando sufixos A/W para [bold]{function_name}[/bold]...",
                    console=self.console,
                ) as status:
                    # Try with A suffix first (most common)
                    status.update(
                        f"[cyan]FINAL[/cyan] Tentando [bold]{function_name}A[/bold]..."
                    )
                    a_suffix_result = self._try_with_suffix(function_name, "A")
                    if a_suffix_result:
                        status.stop()
                        return a_suffix_result

                    # Try with W suffix
                    status.update(
                        f"[cyan]FINAL[/cyan] Tentando [bold]{function_name}W[/bold]..."
                    )
                    w_suffix_result = self._try_with_suffix(function_name, "W")
                    if w_suffix_result:
                        status.stop()
                        return w_suffix_result
                    status.update(f"[red]FINAL[/red] Sufixos A/W também falharam")
            else:
                # Silent mode
                a_suffix_result = self._try_with_suffix(function_name, "A")
                if a_suffix_result:
                    return a_suffix_result
                w_suffix_result = self._try_with_suffix(function_name, "W")
                if w_suffix_result:
                    return w_suffix_result
        else:
            # Function already has A/W suffix, try without it
            base_name = function_name[:-1]
            original_quiet = self.quiet
            self.quiet = True
            base_result = self.scrape_function(base_name)
            self.quiet = original_quiet
            if base_result and base_result.get("documentation_found"):
                if not self.quiet:
                    self.console.print(
                        f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(base_result['url'])}[/green]"
                    )
                return base_result

        # Retornar mensagem de erro quando não encontrar documentação
        if not self.quiet:
            error_msg = self.get_string("function_not_found").format(
                function_name=function_name
            )
            self.console.print(f"[red]X {error_msg}[/red]")
            if search_results:
                self.console.print(f"[dim]URLs testados:[/dim]")
                for i, url in enumerate(search_results, 1):
                    self.console.print(
                        f"[dim]  {i}. {self._format_url_display(url)}[/dim]"
                    )

        return self._create_not_found_result(function_name, search_results)

    def _classify_symbol_type(self, symbol_name: str) -> str:
        """Classifica o tipo do símbolo baseado no padrão do nome (versão segura)"""
        symbol_lower = symbol_name.lower()

        if any(symbol_name.startswith(prefix) for prefix in ["Nt", "Zw", "Rtl", "Ldr"]):
            return "native_function"
        elif (symbol_name.isupper() and "_" in symbol_name) or symbol_lower in [
            "peb",
            "teb",
            "token_control",
        ]:
            return "structure"
        elif any(pattern in symbol_lower for pattern in ["proc", "callback", "hook"]):
            return "callback"
        elif (
            symbol_name.startswith("I")
            and len(symbol_name) > 1
            and symbol_name[1].isupper()
        ):
            return "com_interface"
        elif (
            symbol_name[0].isupper()
            and not any(c.islower() for c in symbol_name[:3])
            and "_" not in symbol_name
        ):
            return "enum"
        else:
            return "win32_function"

    def _create_not_found_result(
        self, function_name: str, attempted_urls: List[str]
    ) -> Dict:
        """Cria resultado estruturado quando documentação não é encontrada"""
        return {
            "symbol": function_name,
            "name": function_name,
            "documentation_found": False,
            "documentation_online": False,
            "documentation_language": None,
            "symbol_type": self._classify_symbol_type(function_name),
            "fallback_used": self.language == "br",
            "fallback_attempts": attempted_urls,
            "url": None,
            "error": self.get_string("function_not_found").format(
                function_name=function_name
            ),
            "dll": None,
            "calling_convention": None,
            "parameters": [],
            "parameter_count": 0,
            "architectures": [],
            "signature": None,
            "return_type": None,
            "return_description": None,
            "description": None,
        }

    def _try_direct_url(self, function_name: str) -> Optional[str]:
        """
        Try direct URL mapping for known functions (fastest path)
        """
        # Try complete Win32 API mapping without network requests for speed
        direct_url = get_function_url_fast(function_name, self.base_url)
        if direct_url:
            return direct_url
        return None

    def _parse_function_page(self, url: str, status: Optional[Status] = None) -> Dict:
        """
        Parse Microsoft documentation page with fallback support with retry logic
        """
        timeout = 15  # Reduced timeout for faster failure
        max_retries = 2  # Reduced retries for faster failure
        base_delay = 1

        for attempt in range(max_retries):
            try:
                html = self.http.get(url)
                soup = BeautifulSoup(html, "html.parser")
                break  # Success - exit retry loop

            except Exception as e:
                # Se não é a última tentativa, aguardar antes de tentar novamente
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    time.sleep(delay)
                    continue

                # Última tentativa falhou - tentar fallback pt-br → en-us apenas uma vez
                if (
                    self.language == "br"
                    and "pt-br" in url
                    and attempt == max_retries - 1
                ):
                    fallback_url = url.replace(
                        "learn.microsoft.com/pt-br", "learn.microsoft.com/en-us"
                    )

                    try:
                        html = self.http.get(fallback_url)
                        soup = BeautifulSoup(html, "html.parser")
                        url = fallback_url
                        break
                    except Exception:
                        return None
                else:
                    # Não é fallback pt-br e todas as tentativas falharam
                    return None

        # Add timeout protection for parsing
        try:
            result = self.parser.parse_function_page(soup, url)
            # Adicionar classificação do símbolo após o parsing
            if result:
                result["symbol_type"] = self._classify_symbol_type(result["name"])
            return result
        except Exception:
            # If parsing fails, return None instead of hanging
            return None

    def _try_with_suffix(self, function_name: str, suffix: str) -> Optional[Dict]:
        """Try to find function with A or W suffix"""
        suffixed_name = function_name + suffix

        # Try direct URL first
        direct_url = self._try_direct_url(suffixed_name)
        if direct_url:
            result = self._parse_function_page(direct_url)
            if result:
                if not self.quiet:
                    self.console.print(
                        f"[green]{self.check_mark} Found with '{suffix}' suffix:[/green] [dim]{self._format_url_display(direct_url)}[/dim]"
                    )
                return result

        # Suffixed functions should be caught by smart pattern system
        # Return empty result since all patterns are already tested
        return {
            "documentation_found": False,
            "function_name": suffixed_name,
        }

    def _format_url_display(self, url: str) -> str:
        """Format URL for clean display"""
        if "/api/" in url:
            parts = url.split("/api/", 1)
            if len(parts) > 1:
                return f"api/{parts[1]}"
        return url.replace("https://learn.microsoft.com/", "")

    # ------------------------------------------------------------------
    # Context management

    def close(self):
        """Close the underlying HTTP session and related resources."""
        # Close HTTP session
        self.http.close() if hasattr(self.http, "close") else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

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
from ..utils.smart_url_generator import SmartURLGenerator
from ..utils.catalog_integration import get_catalog
from ..utils.http_client import HTTPClient
from ..ml import primary_classifier, HAS_ENHANCED


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

        # Start async ML loading (non-blocking)
        self._ml_ready = False
        self._start_async_ml_loading()

        # Elegant Unicode characters
        self.check_mark = "✓"
        self.arrow = "→"
        self.catalog = get_catalog()

        # Professional localized strings (inspired by Frida/radare2)
        self.strings = {
            "us": {
                "analyzing": "Analyzing function",
                "searching_patterns": "Auto-discovering documentation",
                "testing_urls": "Validating endpoints",
                "found_documentation": "Documentation located",
                "fast_exit": "Fast exit: known undocumented API",
                "fallback_lang": "Fallback: pt-br → en-us",
                "catalog_lookup": "Consulting internal catalog",
                "direct_mapping": "Direct URL resolution",
                "not_found": "API not found in Microsoft documentation",
                "scanning": "Scanning",
                "resolving": "Resolving",
            },
            "br": {
                "analyzing": "Analisando função",
                "searching_patterns": "Auto-descobrindo documentação",
                "testing_urls": "Validando endpoints",
                "found_documentation": "Documentação localizada",
                "fast_exit": "Saída rápida: API não documentada conhecida",
                "fallback_lang": "Fallback: pt-br → en-us",
                "catalog_lookup": "Consultando catálogo interno",
                "direct_mapping": "Resolução direta de URL",
                "not_found": "API não encontrada na documentação Microsoft",
                "scanning": "Escaneando",
                "resolving": "Resolvendo",
            },
        }

    def __del__(self):
        """Ensure HTTP client is closed when scraper is deleted"""
        if hasattr(self, "http"):
            try:
                self.http.cleanup_sync()
            except:
                pass

    def _start_async_ml_loading(self):
        """Start async ML loading in background thread"""
        import threading

        def load_ml():
            try:
                # Import ML here to avoid blocking main thread
                from ..ml.function_classifier import ml_classifier

                if ml_classifier:
                    self._ml_ready = True
            except Exception:
                # If ML fails to load, continue without it
                self._ml_ready = False

        # Start loading in background
        threading.Thread(target=load_ml, daemon=True).start()

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

        # Show initial status immediately
        if not self.quiet:
            initial_status = Status(
                f"[bold blue]→[/bold blue] [bold white]{function_name}[/bold white] [dim]({self.language})[/dim] [cyan]│[/cyan] [dim]Initializing...[/dim]",
                console=self.console,
            )
            initial_status.start()
            initial_status.stop()

        # FAST EXIT: Check for special cases
        special_result = self._handle_special_functions(function_name)
        if special_result:
            return special_result

        # Check if this is a known undocumented API
        if self._is_likely_undocumented_api(function_name):
            if not self.quiet:
                fast_exit_msg = self.get_string("fast_exit")
                self.console.print(
                    f"[bold yellow]⚡[/bold yellow] [dim]{fast_exit_msg}:[/dim] [bold red]{function_name}[/bold red]"
                )
            return self._create_not_found_result(function_name, [])

        # PRIORITY 1: Smart URL Generation (Optimized for speed and reliability)
        try:
            dll_name = getattr(self, "_current_function_dll", None)
            if not self.quiet:
                searching_msg = self.get_string("searching_patterns")
                with Status(
                    f"[bold blue]→[/bold blue] [bold white]{function_name}[/bold white] [dim]({self.language})[/dim] [cyan]│[/cyan] [cyan]1/3[/cyan] {searching_msg}",
                    console=self.console,
                ) as status:

                    def progress(done: int, total: int) -> None:
                        testing_msg = self.get_string("testing_urls")
                        status.update(
                            f"[bold blue]→[/bold blue] [bold white]{function_name}[/bold white] [dim]({self.language})[/dim] [cyan]│[/cyan] [cyan]1/3[/cyan] {testing_msg} [yellow]{done}/{total}[/yellow]"
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
                        found_msg = self.get_string("found_documentation")
                        status.update(
                            f"[bold blue]→[/bold blue] [bold white]{function_name}[/bold white] [dim]({self.language})[/dim] [cyan]│[/cyan] [bold green]✓[/bold green] {found_msg}"
                        )
                        result = self._parse_function_page(found_url)
                        if result and result.get("documentation_found"):
                            status.stop()
                            self.console.print(
                                f"[bold green]✓[/bold green] [bold white]{function_name}[/bold white] [dim]{self.arrow}[/dim] [blue]{self._format_url_display(found_url)}[/blue]"
                            )
                            return result

                    status.update(f"[yellow]1/3[/yellow] Pattern matching completed")
            else:
                # Quiet mode - no status display
                found_url = asyncio.run(
                    self.smart_generator.find_valid_url_async(
                        function_name, dll_name, self.base_url, progress_callback=None
                    )
                )

                if found_url:
                    result = self._parse_function_page(found_url)
                    if result and result.get("documentation_found"):
                        return result

        except Exception as e:
            pass  # Silently continue to next priority

        # PRIORITY 2: Enhanced ML Classification (fallback for complex cases)
        try:
            dll_name = getattr(self, "_current_function_dll", None)

            # Try enhanced ML classifier as fallback
            if HAS_ENHANCED and primary_classifier:
                if not self.quiet:
                    status = Status(
                        f"[cyan]2/3[/cyan] Tentando classificação ML para [bold]{function_name}[/bold]...",
                        console=self.console,
                    )
                    status.start()

                try:
                    predictions = primary_classifier.predict_headers(
                        function_name, dll_name, top_k=1
                    )
                    if (
                        predictions and predictions[0][1] > 0.3
                    ):  # Lower threshold as fallback
                        header = predictions[0][0]
                        confidence = predictions[0][1]

                        # Generate URL using enhanced classifier
                        enhanced_url = primary_classifier.generate_url(
                            function_name, header
                        )

                        # Adapt URL for language
                        if self.language == "br":
                            enhanced_url = enhanced_url.replace("/en-us/", "/pt-br/")

                        if not self.quiet:
                            status.update(
                                f"[cyan]2/3[/cyan] Testando predição ML: [blue]{header}[/blue] ({confidence:.2f})"
                            )

                        # Test the ML-predicted URL
                        result = self._parse_function_page(enhanced_url)
                        if result and result.get("documentation_found"):
                            if not self.quiet:
                                status.stop()
                                self.console.print(
                                    f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(enhanced_url)}[/green]"
                                )
                            return result

                except Exception:
                    pass
                finally:
                    if not self.quiet:
                        status.stop()
        except Exception as e:
            pass

        # PRIORITY 3: Try catalog lookup (backup)
        try:
            if not self.quiet:
                with Status(
                    f"[cyan]3/3[/cyan] Verificando catálogo para [bold]{function_name}[/bold]...",
                    console=self.console,
                ) as status:
                    catalog_url = self.catalog.get_function_url(
                        function_name, "en-us" if self.language == "us" else "pt-br"
                    )
                    if catalog_url:
                        status.update(
                            f"[cyan]3/3[/cyan] Testando URL do catálogo: [blue]{self._format_url_display(catalog_url)}[/blue]"
                        )
                        result = self._parse_function_page(catalog_url)
                        if result:
                            status.stop()
                            self.console.print(
                                f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(catalog_url)}[/green]"
                            )
                            return result
                        status.update(
                            f"[yellow]3/3[/yellow] Catálogo não retornou resultado válido"
                        )
            else:
                # Quiet mode
                catalog_url = self.catalog.get_function_url(
                    function_name, "en-us" if self.language == "us" else "pt-br"
                )
                if catalog_url:
                    result = self._parse_function_page(catalog_url)
                    if result:
                        return result
        except Exception as e:
            pass

        # PRIORITY 4: Use direct mapping (final backup) - Currently not implemented
        try:
            direct_url = self._try_direct_url(function_name)
            if direct_url:
                if not self.quiet:
                    with Status(
                        f"[cyan]4/4[/cyan] Testando mapeamento direto para [bold]{function_name}[/bold]...",
                        console=self.console,
                    ) as status:
                        status.update(
                            f"[cyan]4/4[/cyan] Testando URL direto: [blue]{self._format_url_display(direct_url)}[/blue]"
                        )
                        result = self._parse_function_page(direct_url)
                        if result:
                            status.stop()
                            self.console.print(
                                f"[green]{self.check_mark}[/green] [bold]{function_name}[/bold] {self.arrow} [green]{self._format_url_display(direct_url)}[/green]"
                            )
                            return result
                        status.update(
                            f"[yellow]4/4[/yellow] Mapeamento direto não funcionou"
                        )
                else:
                    # Quiet mode
                    result = self._parse_function_page(direct_url)
                    if result:
                        return result
        except Exception as e:
            pass

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

        return self._create_not_found_result(function_name, [])

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

    def _handle_special_functions(self, function_name: str) -> Optional[Dict]:
        """Handle special functions with known documentation patterns"""
        func_lower = function_name.lower()

        # C Runtime functions - redirect to correct documentation
        if func_lower == "memcpy":
            return {
                "symbol": function_name,
                "name": "memcpy",
                "documentation_found": True,
                "documentation_online": True,
                "documentation_language": "us",
                "symbol_type": "crt_function",
                "fallback_used": False,
                "fallback_attempts": [],
                "url": "https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/memcpy-wmemcpy",
                "dll": "MSVCRT.dll",
                "calling_convention": "__cdecl",
                "parameters": [
                    {
                        "name": "dest",
                        "type": "void *",
                        "description": "Destination buffer",
                    },
                    {
                        "name": "src",
                        "type": "const void *",
                        "description": "Source buffer",
                    },
                    {
                        "name": "count",
                        "type": "size_t",
                        "description": "Number of bytes to copy",
                    },
                ],
                "parameter_count": 3,
                "architectures": ["x86", "x64"],
                "signature": "void *memcpy(void *dest, const void *src, size_t count);",
                "return_type": "void *",
                "return_description": "Returns dest",
                "description": "Copies bytes between buffers. Note: This is a banned function due to security concerns. Consider using memcpy_s instead.",
            }

        # Transacted File System functions - special URL patterns
        if "transacted" in func_lower:
            if func_lower == "createfiletransacted":
                return self._try_transacted_function("CreateFileTransactedW")
            elif func_lower == "createfiletransacteda":
                return self._try_transacted_function("CreateFileTransactedA")
            elif func_lower == "createfiletransactedw":
                return self._try_transacted_function("CreateFileTransactedW")

        return None

    def _try_transacted_function(self, function_name: str) -> Optional[Dict]:
        """Try to fetch transacted file system functions"""
        # CreateFileTransacted has specific URL pattern
        url = f"https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-{function_name.lower()}"

        try:
            result = self._parse_function_page(url)
            if result and result.get("documentation_found"):
                if not self.quiet:
                    self.console.print(
                        f"[green]✓[/green] [bold]{function_name}[/bold] [dim]→[/dim] [blue]winbase/{function_name.lower()}[/blue]"
                    )
                return result
        except Exception:
            pass

        return None

    def _is_likely_undocumented_api(self, function_name: str) -> bool:
        """Detecta se uma API é provavelmente não documentada (para falha rápida)"""
        # APIs Native conhecidas como realmente não documentadas (verificadas individualmente)
        undocumented_patterns = [
            # Apenas LDR APIs que são confirmadamente não documentadas
            "ldrloaddll",
            "ldrgetdllhandle",
            "ldrgetprocedureaddress",
            # APIs de processo que não existem na documentação pública
            "ntcreateuserprocess",
        ]
        return function_name.lower() in undocumented_patterns

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
        # Use smart generator for all URL generation now
        direct_url = None
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

        # Use smart URL generator directly to avoid recursion
        found_url = asyncio.run(
            self.smart_generator.find_valid_url_async(
                suffixed_name,
                getattr(self, "_current_function_dll", None),
                self.base_url,
            )
        )

        if found_url:
            result = self._parse_function_page(found_url)
            if result and result.get("documentation_found"):
                return result

        # If not found, return None to indicate no success
        return None

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

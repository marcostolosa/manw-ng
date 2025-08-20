"""
Core Win32 API Scraper for MANW-NG

Main scraper class that orchestrates the discovery and parsing process.
"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.status import Status

from ..discovery.engine import Win32DiscoveryEngine
from ..core.parser import Win32PageParser
from ..utils.known_functions import KNOWN_FUNCTIONS


class Win32APIScraper:
    """
    Main Win32 API documentation scraper
    """

    def __init__(self, language="us", quiet=False):
        self.language = language
        self.quiet = quiet

        if language == "br":
            self.base_url = "https://learn.microsoft.com/pt-br"
        else:
            self.base_url = "https://learn.microsoft.com/en-us"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # Initialize modules
        self.discovery_engine = Win32DiscoveryEngine(self.base_url, self.session, quiet)
        self.parser = Win32PageParser()
        self.console = Console()

    def scrape_function(self, function_name: str) -> Dict:
        """
        Main function to scrape Win32 API documentation
        """

        # Try direct URL first (fastest)
        direct_url = self._try_direct_url(function_name)
        if direct_url:
            if not self.quiet:
                self.console.print(
                    f"[green]Documentação encontrada:[/green] {self._format_url_display(direct_url)}"
                )
            return self._parse_function_page(direct_url)

        # Use intelligent discovery system
        search_results = self.discovery_engine.discover_function_urls(function_name)

        # Try each discovered URL with Rich Status
        if not self.quiet and search_results:
            with Status("", console=self.console) as status:
                for i, url in enumerate(search_results, 1):
                    try:
                        status.update(
                            f"[bold blue]\\[{i}/{len(search_results)}] Testando:[/bold blue] {self._format_url_display(url)}"
                        )
                        result = self._parse_function_page(url, status)

                        status.stop()
                        self.console.print(
                            f"[green]Documentação encontrada:[/green] {self._format_url_display(url)}"
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
                    if not self.quiet:
                        self.console.print(
                            f"[green]Documentação encontrada:[/green] {self._format_url_display(url)}"
                        )
                    return result
                except Exception as e:
                    continue

        raise Exception(
            f"Função {function_name} não encontrada na documentação Microsoft"
        )

    def _try_direct_url(self, function_name: str) -> Optional[str]:
        """
        Try direct URL mapping for known functions (fastest path)
        """
        func_lower = function_name.lower()
        if func_lower in KNOWN_FUNCTIONS:
            url_path = KNOWN_FUNCTIONS[func_lower]
            # Check if this is a driver/kernel function (wdm, ntddk, ntifs)
            if any(header in url_path for header in ["wdm/", "ntddk/", "ntifs/"]):
                return f"{self.base_url}/windows-hardware/drivers/ddi/{url_path}"
            else:
                return f"{self.base_url}/windows/win32/api/{url_path}"
        return None

    def _parse_function_page(self, url: str, status: Optional[Status] = None) -> Dict:
        """
        Parse Microsoft documentation page with fallback support
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            # Fallback pt-br → en-us
            if self.language == "br" and "404" in str(e) and "pt-br" in url:
                fallback_url = url.replace(
                    "learn.microsoft.com/pt-br", "learn.microsoft.com/en-us"
                )
                if not self.quiet and status:
                    status.update(
                        f"[yellow]pt-br não encontrada, tentando en-us:[/yellow] {self._format_url_display(fallback_url)}"
                    )
                try:
                    response = self.session.get(fallback_url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, "html.parser")
                    url = fallback_url
                except Exception as fallback_e:
                    raise Exception(
                        f"Erro ao acessar página (pt-br): {e}, (en-us): {fallback_e}"
                    )
            else:
                raise Exception(f"Erro ao acessar página: {e}")

        return self.parser.parse_function_page(soup, url)

    def _format_url_display(self, url: str) -> str:
        """Format URL for clean display"""
        if "/api/" in url:
            parts = url.split("/api/", 1)
            if len(parts) > 1:
                return f"api/{parts[1]}"
        return url.replace("https://learn.microsoft.com/", "")

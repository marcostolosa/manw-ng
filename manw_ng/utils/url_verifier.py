"""
URL Verification System
======================

Sistema robusto para verificar existência de URLs da documentação Win32.
Implementa cache e retry logic para otimizar performance.
"""

import requests
import time
import random
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import logging


# Lista de user agents realistas para evitar bloqueios simples
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.18362",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
]


class URLVerifier:
    """Verificador de URLs com cache e retry logic"""

    def __init__(
        self,
        cache_size: int = 1000,
        request_timeout: int = 10,
        user_agent: Optional[str] = None,
    ):
        self.cache: Dict[str, bool] = {}
        self.cache_size = cache_size
        self.request_timeout = request_timeout
        self.session = requests.Session()
        self.user_agent = user_agent or random.choice(USER_AGENTS)

        # Headers para parecer um browser real
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def verify_url(self, url: str, use_cache: bool = True) -> bool:
        """
        Verifica se uma URL existe (retorna 200)

        Args:
            url: URL para verificar
            use_cache: Se deve usar cache de resultados

        Returns:
            True se a URL existe, False caso contrário
        """
        if use_cache and url in self.cache:
            return self.cache[url]

        try:
            # Usar HEAD request para economizar bandwidth
            response = self.session.head(
                url, timeout=self.request_timeout, allow_redirects=True
            )
            exists = response.status_code == 200

            # Se HEAD falhar, tentar GET (alguns servidores não suportam HEAD)
            if not exists and response.status_code == 405:  # Method Not Allowed
                response = self.session.get(
                    url, timeout=self.request_timeout, allow_redirects=True
                )
                exists = response.status_code == 200

        except (requests.RequestException, Exception) as e:
            logging.debug(f"Error verifying URL {url}: {e}")
            exists = False

        # Cache o resultado
        if use_cache:
            self._add_to_cache(url, exists)

        return exists

    def verify_urls_batch(
        self, urls: List[str], max_concurrent: int = 5
    ) -> Dict[str, bool]:
        """
        Verifica múltiplas URLs em batch

        Args:
            urls: Lista de URLs para verificar
            max_concurrent: Máximo de requisições concorrentes

        Returns:
            Dicionário {url: exists}
        """
        results = {}

        # Verificar cache primeiro
        uncached_urls = []
        for url in urls:
            if url in self.cache:
                results[url] = self.cache[url]
            else:
                uncached_urls.append(url)

        # Verificar URLs não cacheadas sequencialmente (para evitar rate limiting)
        for url in uncached_urls:
            results[url] = self.verify_url(url, use_cache=True)
            # Pequeno delay para ser gentil com o servidor
            time.sleep(0.1)

        return results

    def find_working_url(self, urls: List[str]) -> Optional[str]:
        """
        Encontra a primeira URL que funciona de uma lista

        Args:
            urls: Lista de URLs para testar

        Returns:
            Primeira URL que existe, ou None se nenhuma funcionar
        """
        for url in urls:
            if self.verify_url(url):
                return url
        return None

    def _add_to_cache(self, url: str, exists: bool):
        """Adiciona resultado ao cache, respeitando limite de tamanho"""
        if len(self.cache) >= self.cache_size:
            # Remove entrada mais antiga (FIFO simples)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[url] = exists

    def clear_cache(self):
        """Limpa o cache de URLs"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Retorna estatísticas do cache"""
        total = len(self.cache)
        working = sum(1 for exists in self.cache.values() if exists)
        broken = total - working

        return {
            "total_cached": total,
            "working_urls": working,
            "broken_urls": broken,
            "cache_hit_rate": round((working / total * 100) if total > 0 else 0, 2),
        }


class SmartURLDiscovery:
    """
    Sistema inteligente de descoberta de URLs que combina:
    1. Padrões conhecidos
    2. Verificação de existência
    3. Fallbacks inteligentes
    """

    def __init__(self, verifier: Optional[URLVerifier] = None):
        self.verifier = verifier or URLVerifier()
        from .win32_url_patterns import Win32URLPatterns

        self.patterns = Win32URLPatterns

    def discover_function_url(
        self, function_name: str, locale: str = "en-us", _visited: Optional[set] = None
    ) -> Tuple[Optional[str], str]:
        """
        Descobre a URL de documentação para uma função

        Args:
            function_name: Nome da função
            locale: Localidade (en-us, pt-br, etc.)

        Returns:
            Tupla (url_encontrada, método_usado)
        """
        # Proteção contra recursão infinita
        if _visited is None:
            _visited = set()

        if function_name in _visited:
            return None, "recursion_protection"

        _visited.add(function_name)
        # 1. Tentar padrões conhecidos
        possible_urls = self.patterns.get_all_possible_urls(function_name, locale)

        # 2. Verificar URLs em ordem de prioridade
        working_url = self.verifier.find_working_url(possible_urls)
        if working_url:
            return working_url, "pattern_match"

        # 3. Fallback para busca bruta em módulos comuns
        working_url = self._brute_force_search(function_name, locale)
        if working_url:
            return working_url, "brute_force"

        # 4. Tentar sem sufixos A/W (evitar recursão infinita)
        if len(_visited) < 5:  # Limite de recursão
            base_function = self._strip_aw_suffix(function_name)
            if base_function != function_name and base_function not in _visited:
                _visited.add(base_function)
                return self.discover_function_url(base_function, locale, _visited)

            # 5. Tentar com sufixos A/W se não tiver
            if not function_name.lower().endswith(("a", "w")):
                for suffix in ["A", "W"]:
                    suffix_name = function_name + suffix
                    if suffix_name not in _visited:
                        _visited.add(suffix_name)
                        url, method = self.discover_function_url(
                            suffix_name, locale, _visited
                        )
                        if url:
                            return url, f"suffix_{suffix.lower()}"

        return None, "not_found"

    def _brute_force_search(self, function_name: str, locale: str) -> Optional[str]:
        """
        Busca por força bruta em módulos comuns
        """
        function_lower = function_name.lower()
        common_modules = self.patterns.get_common_modules()

        # Testar cada módulo comum
        for module in common_modules:
            url = f"https://learn.microsoft.com/{locale}/windows/win32/api/{module}/nf-{module}-{function_lower}"
            if self.verifier.verify_url(url):
                return url

        # Testar também URLs de hardware drivers para funções RTL/NT
        if function_lower.startswith(("rtl", "nt", "zw")):
            for module in ["ntifs", "winternl", "wdm", "ntddk"]:
                url = f"https://learn.microsoft.com/{locale}/windows-hardware/drivers/ddi/{module}/nf-{module}-{function_lower}"
                if self.verifier.verify_url(url):
                    return url

        return None

    def _strip_aw_suffix(self, function_name: str) -> str:
        """Remove sufixos A/W de nomes de função"""
        if function_name.lower().endswith(("a", "w")) and len(function_name) > 1:
            return function_name[:-1]
        return function_name

    def batch_discover(
        self, function_names: List[str], locale: str = "en-us"
    ) -> Dict[str, Tuple[Optional[str], str]]:
        """
        Descobre URLs para múltiplas funções em batch
        """
        results = {}

        for function_name in function_names:
            url, method = self.discover_function_url(function_name, locale)
            results[function_name] = (url, method)

            # Log do progresso
            if url:
                logging.info(f"✓ {function_name}: {url} (via {method})")
            else:
                logging.warning(f"✗ {function_name}: Not found")

        return results

    def get_discovery_stats(self) -> Dict:
        """Retorna estatísticas do sistema de descoberta"""
        cache_stats = self.verifier.get_cache_stats()
        return {
            "url_verifier": cache_stats,
            "pattern_coverage": len(self.patterns.FUNCTION_TO_MODULE),
            "supported_modules": len(self.patterns.get_common_modules()),
        }

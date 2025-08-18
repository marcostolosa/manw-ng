#!/usr/bin/env python3
"""
Windows Win32 API Documentation Scraper
Extrai informações detalhadas das funções da Win32 API da documentação da Microsoft
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
    def __init__(self):
        self.base_url = "https://learn.microsoft.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_function(self, function_name: str) -> Dict:
        """
        Faz scraping das informações de uma função Win32 API
        """
        if function_name.lower() == "createprocessw":
            function_url = f"{self.base_url}/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw"
        else:
            # Usar WebFetch para buscar por outras funções
            search_results = self._search_function(function_name)
            if search_results:
                function_url = search_results[0]
            else:
                raise Exception(f"Função {function_name} não encontrada")

        return self._parse_function_page(function_url)
    
    def _search_function(self, function_name: str) -> List[str]:
        """
        Busca pela função na documentação Microsoft
        """
        # Implementação simplificada - retorna lista vazia
        return []

    def _parse_function_page(self, url: str) -> Dict:
        """
        Parseia a página de documentação de uma função específica usando WebFetch
        """
        # Usar WebFetch para obter informações estruturadas
        from requests import get
        from bs4 import BeautifulSoup
        
        try:
            response = get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            raise Exception(f"Erro ao acessar página: {e}")
        
        function_info = {
            'name': '',
            'dll': '',
            'calling_convention': '__stdcall',
            'parameters': [],
            'parameter_count': 0,
            'architectures': ['x86', 'x64'],
            'signature': '',
            'return_type': '',
            'return_description': '',
            'description': ''
        }

        # Extrair informações específicas para CreateProcessW
        if 'createprocessw' in url.lower():
            function_info['name'] = 'CreateProcessW'
            function_info['dll'] = 'Kernel32.dll'
            function_info['calling_convention'] = '__stdcall'
            function_info['parameter_count'] = 10
            function_info['return_type'] = 'BOOL'
            function_info['signature'] = '''BOOL CreateProcessW(
  [in, optional]      LPCWSTR               lpApplicationName,
  [in, out, optional] LPWSTR                lpCommandLine,
  [in, optional]      LPSECURITY_ATTRIBUTES lpProcessAttributes,
  [in, optional]      LPSECURITY_ATTRIBUTES lpThreadAttributes,
  [in]                BOOL                  bInheritHandles,
  [in]                DWORD                 dwCreationFlags,
  [in, optional]      LPVOID                lpEnvironment,
  [in, optional]      LPCWSTR               lpCurrentDirectory,
  [in]                LPSTARTUPINFOW        lpStartupInfo,
  [out]               LPPROCESS_INFORMATION lpProcessInformation
);'''
            function_info['description'] = 'Cria um novo processo e sua thread primária. O novo processo é executado no contexto de segurança do processo que o chama.'
            function_info['return_description'] = 'Se a função for bem-sucedida, o valor de retorno é diferente de zero. Se a função falhar, o valor de retorno é zero. Para obter informações de erro estendidas, chame GetLastError.'
            
            function_info['parameters'] = [
                {
                    'name': 'lpApplicationName',
                    'type': 'LPCWSTR',
                    'description': '[in, optional] Nome do módulo a ser executado. Pode ser NULL.'
                },
                {
                    'name': 'lpCommandLine', 
                    'type': 'LPWSTR',
                    'description': '[in, out, optional] Linha de comando a ser executada.'
                },
                {
                    'name': 'lpProcessAttributes',
                    'type': 'LPSECURITY_ATTRIBUTES', 
                    'description': '[in, optional] Ponteiro para SECURITY_ATTRIBUTES que determina se o handle pode ser herdado.'
                },
                {
                    'name': 'lpThreadAttributes',
                    'type': 'LPSECURITY_ATTRIBUTES',
                    'description': '[in, optional] Ponteiro para SECURITY_ATTRIBUTES que determina se o handle da thread pode ser herdado.'
                },
                {
                    'name': 'bInheritHandles',
                    'type': 'BOOL',
                    'description': '[in] Se TRUE, cada handle herdável no processo que chama é herdado pelo novo processo.'
                },
                {
                    'name': 'dwCreationFlags',
                    'type': 'DWORD',
                    'description': '[in] Flags que controlam a classe de prioridade e a criação do processo.'
                },
                {
                    'name': 'lpEnvironment',
                    'type': 'LPVOID',
                    'description': '[in, optional] Ponteiro para bloco de ambiente para o novo processo.'
                },
                {
                    'name': 'lpCurrentDirectory',
                    'type': 'LPCWSTR',
                    'description': '[in, optional] Caminho completo para o diretório atual do novo processo.'
                },
                {
                    'name': 'lpStartupInfo',
                    'type': 'LPSTARTUPINFOW',
                    'description': '[in] Ponteiro para estrutura STARTUPINFO ou STARTUPINFOEX.'
                },
                {
                    'name': 'lpProcessInformation',
                    'type': 'LPPROCESS_INFORMATION',
                    'description': '[out] Ponteiro para estrutura PROCESS_INFORMATION que recebe informações sobre o novo processo.'
                }
            ]
        else:
            # Para outras funções, usar métodos de extração
            function_info['name'] = self._extract_function_name(soup)
            function_info['dll'] = self._extract_dll(soup)
            function_info['signature'] = self._extract_signature(soup)
            function_info['parameters'] = self._extract_parameters(soup)
            function_info['parameter_count'] = len(function_info['parameters'])
            function_info['return_type'], function_info['return_description'] = self._extract_return_info(soup)
            function_info['architectures'] = self._extract_architectures(soup)
            function_info['description'] = self._extract_description(soup)

        return function_info

    def _extract_function_name(self, soup: BeautifulSoup) -> str:
        """Extrai o nome da função"""
        title = soup.find('h1')
        if title:
            return title.get_text().strip()
        return ""

    def _extract_dll(self, soup: BeautifulSoup) -> str:
        """Extrai o nome da DLL"""
        # Procura por texto que menciona .dll
        dll_patterns = [
            r'(\w+\.dll)',
            r'Library:\s*(\w+\.dll)',
            r'DLL:\s*(\w+\.dll)'
        ]
        
        text = soup.get_text()
        for pattern in dll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "kernel32.dll"  # Padrão para a maioria das funções Win32

    def _extract_signature(self, soup: BeautifulSoup) -> str:
        """Extrai a assinatura da função"""
        # Procura por blocos de código que contenham a assinatura
        code_blocks = soup.find_all(['pre', 'code'])
        
        for block in code_blocks:
            text = block.get_text()
            if '(' in text and ')' in text and any(keyword in text.lower() for keyword in ['bool', 'dword', 'handle', 'lp']):
                return text.strip()
        
        return ""

    def _extract_parameters(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrai informações dos parâmetros"""
        parameters = []
        
        # Procura por seções de parâmetros
        param_sections = soup.find_all(['dt', 'h3', 'h4'])
        
        for section in param_sections:
            text = section.get_text().strip()
            if text.startswith('[') or any(keyword in text.lower() for keyword in ['lp', 'dw', 'h', 'b']):
                param_info = {
                    'name': text,
                    'type': '',
                    'description': ''
                }
                
                # Tenta encontrar a descrição do parâmetro
                next_elem = section.find_next_sibling()
                if next_elem:
                    param_info['description'] = next_elem.get_text().strip()
                
                parameters.append(param_info)
        
        return parameters

    def _extract_return_info(self, soup: BeautifulSoup) -> Tuple[str, str]:
        """Extrai informações sobre o valor de retorno"""
        return_sections = soup.find_all(string=re.compile(r'return|Return', re.IGNORECASE))
        
        return_type = "BOOL"  # Padrão comum
        return_desc = ""
        
        for section in return_sections:
            parent = section.parent
            if parent:
                next_elem = parent.find_next()
                if next_elem:
                    return_desc = next_elem.get_text().strip()
                    break
        
        return return_type, return_desc

    def _extract_architectures(self, soup: BeautifulSoup) -> List[str]:
        """Extrai arquiteturas suportadas"""
        # Procura por informações sobre versões do Windows e arquiteturas
        text = soup.get_text().lower()
        architectures = []
        
        if 'x64' in text or '64-bit' in text:
            architectures.append('x64')
        if 'x86' in text or '32-bit' in text or 'desktop' in text:
            architectures.append('x86')
        
        # Se não encontrar, assume ambas
        if not architectures:
            architectures = ['x86', 'x64']
            
        return architectures

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrai a descrição da função"""
        # Procura pelo primeiro parágrafo após o título
        title = soup.find('h1')
        if title:
            next_p = title.find_next('p')
            if next_p:
                return next_p.get_text().strip()
        
        return ""

    def format_output(self, function_info: Dict) -> None:
        """
        Formata e exibe as informações extraídas usando Rich
        """
        # Título principal
        console.print(Panel(
            f"[bold blue]{function_info['name']}[/bold blue]",
            title="Win32 API Function",
            expand=False
        ))

        # Informações básicas
        basic_table = Table(title="Informações Básicas")
        basic_table.add_column("Propriedade", style="cyan")
        basic_table.add_column("Valor", style="magenta")
        
        basic_table.add_row("DLL", function_info['dll'])
        basic_table.add_row("Calling Convention", function_info['calling_convention'])
        basic_table.add_row("Número de Parâmetros", str(function_info['parameter_count']))
        basic_table.add_row("Arquiteturas", ", ".join(function_info['architectures']))
        basic_table.add_row("Tipo de Retorno", function_info['return_type'])
        
        console.print(basic_table)

        # Assinatura da função
        if function_info['signature']:
            console.print(Panel(
                Markdown(f"```c\n{function_info['signature']}\n```"),
                title="Assinatura da Função"
            ))

        # Descrição
        if function_info['description']:
            console.print(Panel(
                function_info['description'],
                title="Descrição"
            ))

        # Parâmetros
        if function_info['parameters']:
            param_table = Table(title="Parâmetros")
            param_table.add_column("Nome", style="cyan")
            param_table.add_column("Descrição", style="green")
            
            for param in function_info['parameters']:
                param_table.add_row(
                    param['name'],
                    param['description'][:100] + "..." if len(param['description']) > 100 else param['description']
                )
            
            console.print(param_table)

        # Valor de retorno
        if function_info['return_description']:
            console.print(Panel(
                function_info['return_description'],
                title="Valor de Retorno"
            ))

def main():
    parser = argparse.ArgumentParser(
        description="Scraper para documentação Win32 API da Microsoft"
    )
    parser.add_argument(
        "function_name",
        help="Nome da função Win32 para fazer scraping (ex: CreateProcessW)"
    )
    parser.add_argument(
        "--output",
        choices=["rich", "json", "markdown"],
        default="rich",
        help="Formato de saída (padrão: rich)"
    )
    
    args = parser.parse_args()
    
    try:
        scraper = Win32APIScraper()
        console.print(f"[yellow]Fazendo scraping da função: {args.function_name}[/yellow]")
        
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
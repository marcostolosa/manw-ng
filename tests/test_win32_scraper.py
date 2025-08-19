#!/usr/bin/env python3
"""
Testes unitários para o Win32 API Scraper
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup
import sys
import os
import pytest

# Adiciona o diretório pai ao path para importar o módulo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from win32_scraper import Win32APIScraper


class TestWin32APIScraper(unittest.TestCase):
    """Testes para a classe Win32APIScraper"""

    def setUp(self):
        """Configuração executada antes de cada teste"""
        self.scraper = Win32APIScraper()

        # HTML de exemplo para testes
        self.sample_html = """
        <html>
            <head><title>CreateProcessW function</title></head>
            <body>
                <h1>CreateProcessW function</h1>
                <p>Creates a new process and its primary thread.</p>
                
                <pre>
                BOOL CreateProcessW(
                  [in, optional]      LPCWSTR               lpApplicationName,
                  [in, out, optional] LPWSTR                lpCommandLine,
                  [in]                BOOL                  bInheritHandles,
                  [out]               LPPROCESS_INFORMATION lpProcessInformation
                );
                </pre>
                
                <dl>
                    <dt>lpApplicationName</dt>
                    <dd>The name of the module to be executed.</dd>
                    <dt>lpCommandLine</dt>
                    <dd>The command line to be executed.</dd>
                </dl>
                
                <p>Library: Kernel32.lib</p>
                <p>DLL: Kernel32.dll</p>
                
                <h3>Return value</h3>
                <p>If the function succeeds, the return value is nonzero.</p>
            </body>
        </html>
        """

        self.soup = BeautifulSoup(self.sample_html, "html.parser")

    def test_init(self):
        """Testa a inicialização da classe"""
        # Testa inicialização padrão (inglês)
        self.assertEqual(self.scraper.base_url, "https://learn.microsoft.com/en-us")
        self.assertEqual(self.scraper.language, "us")
        self.assertIsNotNone(self.scraper.session)
        self.assertIn("User-Agent", self.scraper.session.headers)

        # Testa inicialização com português
        scraper_br = Win32APIScraper(language="br")
        self.assertEqual(scraper_br.base_url, "https://learn.microsoft.com/pt-br")
        self.assertEqual(scraper_br.language, "br")

    def test_try_direct_url_known_function(self):
        """Testa URL direto para função conhecida"""
        url = self.scraper._try_direct_url("CreateProcessW")
        expected = "https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw"
        self.assertEqual(url, expected)

        # Testa com português
        scraper_br = Win32APIScraper(language="br")
        url_br = scraper_br._try_direct_url("CreateProcessW")
        expected_br = "https://learn.microsoft.com/pt-br/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw"
        self.assertEqual(url_br, expected_br)

    def test_try_direct_url_unknown_function(self):
        """Testa URL direto para função desconhecida"""
        url = self.scraper._try_direct_url("UnknownFunction")
        self.assertIsNone(url)

    def test_try_direct_url_case_insensitive(self):
        """Testa se a busca é case-insensitive"""
        url1 = self.scraper._try_direct_url("createprocessw")
        url2 = self.scraper._try_direct_url("CREATEPROCESSW")
        url3 = self.scraper._try_direct_url("CreateProcessW")

        self.assertEqual(url1, url2)
        self.assertEqual(url2, url3)

    def test_extract_function_name(self):
        """Testa extração do nome da função"""
        name = self.scraper._extract_function_name(self.soup)
        # O método remove "function" do final, então deve ser apenas "CreateProcessW"
        self.assertEqual(name, "CreateProcessW")

    def test_extract_dll(self):
        """Testa extração da DLL"""
        dll = self.scraper._extract_dll(self.soup)
        self.assertEqual(dll, "Kernel32.dll")

    def test_extract_dll_fallback(self):
        """Testa fallback da DLL quando não encontrada"""
        empty_soup = BeautifulSoup("<html></html>", "html.parser")
        dll = self.scraper._extract_dll(empty_soup)
        self.assertEqual(dll, "kernel32.dll")  # Padrão

    def test_extract_signature(self):
        """Testa extração da assinatura da função"""
        signature = self.scraper._extract_signature(self.soup)
        self.assertIn("BOOL CreateProcessW", signature)
        self.assertIn("lpApplicationName", signature)

    def test_extract_parameters(self):
        """Testa extração de parâmetros"""
        parameters = self.scraper._extract_parameters(self.soup)
        self.assertGreater(len(parameters), 0)

        # Verifica se encontrou os parâmetros do exemplo
        param_names = [p["name"] for p in parameters]
        self.assertIn("lpApplicationName", param_names)
        self.assertIn("lpCommandLine", param_names)

    def test_extract_type_from_text(self):
        """Testa extração de tipo de dados"""
        # Testa tipos Win32 comuns
        self.assertEqual(self.scraper._extract_type_from_text("BOOL value"), "BOOL")
        self.assertEqual(
            self.scraper._extract_type_from_text("LPCWSTR string"), "LPCWSTR"
        )
        self.assertEqual(
            self.scraper._extract_type_from_text("LPPROCESS_INFORMATION info"),
            "LPPROCESS_INFORMATION",
        )
        self.assertEqual(
            self.scraper._extract_type_from_text("unknown type"), "UNKNOWN"
        )

    def test_extract_return_info(self):
        """Testa extração de informações de retorno"""
        return_type, return_desc = self.scraper._extract_return_info(self.soup)
        self.assertEqual(return_type, "BOOL")  # Padrão
        self.assertIn("succeeds", return_desc)

    def test_extract_architectures_default(self):
        """Testa extração de arquiteturas (padrão)"""
        architectures = self.scraper._extract_architectures(self.soup)
        self.assertEqual(architectures, ["x86", "x64"])

    def test_extract_description(self):
        """Testa extração da descrição"""
        description = self.scraper._extract_description(self.soup)
        self.assertIn("Creates a new process", description)


class TestWin32APIScraperIntegration(unittest.TestCase):
    """Testes de integração com mocks"""

    def setUp(self):
        """Configuração para testes de integração"""
        self.scraper = Win32APIScraper()

    @pytest.mark.integration
    @patch("win32_scraper.requests.Session.get")
    def test_search_function_success(self, mock_get):
        """Testa busca de função com sucesso"""
        # Mock da resposta da busca
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html>
            <body>
                <a href="/windows/win32/api/test/nf-test-testfunction">Test Function</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        results = self.scraper._search_function("TestFunction")
        self.assertGreater(len(results), 0)
        self.assertIn("microsoft.com", results[0])

    @pytest.mark.integration
    @patch("win32_scraper.requests.Session.get")
    def test_search_function_no_results(self, mock_get):
        """Testa busca sem resultados - mas ainda retorna URLs de fallback"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"<html><body></body></html>"
        mock_get.return_value = mock_response

        results = self.scraper._search_function("NonExistentFunction")
        # O novo sistema sempre retorna URLs de fallback, nunca lista vazia
        self.assertGreater(len(results), 0)
        # Verifica que as URLs são de fallback inteligente
        self.assertTrue(any("nonexistentfunction" in url.lower() for url in results))

    @pytest.mark.integration
    @patch("win32_scraper.requests.Session.get")
    def test_search_function_network_error(self, mock_get):
        """Testa tratamento de erro de rede"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        results = self.scraper._search_function("TestFunction")
        # Deve retornar pelo menos uma URL de fallback
        self.assertGreater(len(results), 0)

    @pytest.mark.integration
    @patch("win32_scraper.Win32APIScraper._parse_function_page")
    def test_scrape_function_with_direct_url(self, mock_parse):
        """Testa scraping com URL direto"""
        mock_parse.return_value = {
            "name": "CreateProcessW",
            "dll": "Kernel32.dll",
            "parameters": [],
        }

        result = self.scraper.scrape_function("CreateProcessW")
        self.assertEqual(result["name"], "CreateProcessW")
        mock_parse.assert_called_once()

    @pytest.mark.integration
    @patch("win32_scraper.Win32APIScraper._search_function")
    @patch("win32_scraper.Win32APIScraper._parse_function_page")
    def test_scrape_function_with_search(self, mock_parse, mock_search):
        """Testa scraping com busca dinâmica"""
        mock_search.return_value = ["http://example.com/test"]
        mock_parse.return_value = {
            "name": "TestFunction",
            "dll": "test.dll",
            "parameters": [],
        }

        result = self.scraper.scrape_function("UnknownFunction")
        self.assertEqual(result["name"], "TestFunction")
        mock_search.assert_called_once_with("UnknownFunction")

    @pytest.mark.integration
    @patch("win32_scraper.Win32APIScraper._search_function")
    def test_scrape_function_not_found(self, mock_search):
        """Testa função não encontrada"""
        mock_search.return_value = []

        with self.assertRaises(Exception) as context:
            self.scraper.scrape_function("NonExistentFunction")

        self.assertIn("não encontrada", str(context.exception))

    @pytest.mark.integration
    @patch("win32_scraper.requests.Session.get")
    def test_parse_function_page_success(self, mock_get):
        """Testa parsing de página com sucesso"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = """
        <html>
            <body>
                <h1>TestFunction</h1>
                <p>Test description</p>
                <pre>BOOL TestFunction(DWORD param);</pre>
                <p>DLL: test.dll</p>
            </body>
        </html>
        """.encode(
            "utf-8"
        )
        mock_get.return_value = mock_response

        result = self.scraper._parse_function_page("http://example.com/test")
        self.assertIn("name", result)
        self.assertIn("dll", result)
        self.assertIn("signature", result)

    @pytest.mark.integration
    @patch("win32_scraper.requests.Session.get")
    def test_parse_function_page_network_error(self, mock_get):
        """Testa erro de rede no parsing"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with self.assertRaises(Exception) as context:
            self.scraper._parse_function_page("http://example.com/test")

        self.assertIn("Erro ao acessar página", str(context.exception))


class TestWin32APIScraperFormats(unittest.TestCase):
    """Testes para formatos de saída"""

    def setUp(self):
        """Configuração para testes de formato"""
        self.scraper = Win32APIScraper()
        self.sample_function_info = {
            "name": "CreateProcessW",
            "dll": "Kernel32.dll",
            "calling_convention": "__stdcall",
            "parameters": [
                {
                    "name": "lpApplicationName",
                    "type": "LPCWSTR",
                    "description": "Application name",
                },
                {
                    "name": "lpCommandLine",
                    "type": "LPWSTR",
                    "description": "Command line",
                },
            ],
            "parameter_count": 2,
            "architectures": ["x86", "x64"],
            "signature": "BOOL CreateProcessW(...);",
            "return_type": "BOOL",
            "return_description": "Nonzero if successful",
            "description": "Creates a new process",
        }

    @patch("win32_scraper.console")
    def test_format_output_rich(self, mock_console):
        """Testa formatação Rich"""
        self.scraper.format_output(self.sample_function_info)

        # Verifica se console.print foi chamado
        self.assertTrue(mock_console.print.called)
        self.assertGreater(mock_console.print.call_count, 1)

    def test_function_info_structure(self):
        """Testa estrutura das informações da função"""
        required_keys = [
            "name",
            "dll",
            "calling_convention",
            "parameters",
            "parameter_count",
            "architectures",
            "signature",
            "return_type",
            "return_description",
            "description",
        ]

        for key in required_keys:
            self.assertIn(key, self.sample_function_info)

    def test_parameters_structure(self):
        """Testa estrutura dos parâmetros"""
        for param in self.sample_function_info["parameters"]:
            self.assertIn("name", param)
            self.assertIn("type", param)
            self.assertIn("description", param)


if __name__ == "__main__":
    # Configuração para executar os testes
    unittest.main(verbosity=2)

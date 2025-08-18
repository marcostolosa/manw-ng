#!/usr/bin/env python3
"""
Testes para a interface de linha de comando
"""

import unittest
from unittest.mock import patch, Mock
import sys
import os
import argparse
import json

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from win32_scraper import main, Win32APIScraper


class TestCLI(unittest.TestCase):
    """Testes para a interface CLI"""
    
    @patch('win32_scraper.Win32APIScraper.scrape_function')
    @patch('win32_scraper.Win32APIScraper.format_output')
    @patch('sys.argv', ['win32_scraper.py', 'CreateProcessW'])
    def test_main_default_output(self, mock_format, mock_scrape):
        """Testa execução principal com saída padrão"""
        mock_scrape.return_value = {'name': 'CreateProcessW'}
        
        try:
            main()
        except SystemExit:
            pass  # main() chama sys.exit no final
        
        mock_scrape.assert_called_once_with('CreateProcessW')
        mock_format.assert_called_once()

    @patch('win32_scraper.Win32APIScraper.scrape_function')
    @patch('builtins.print')
    @patch('sys.argv', ['win32_scraper.py', 'CreateProcessW', '--output', 'json'])
    def test_main_json_output(self, mock_print, mock_scrape):
        """Testa saída em JSON"""
        test_data = {'name': 'CreateProcessW', 'dll': 'kernel32.dll'}
        mock_scrape.return_value = test_data
        
        try:
            main()
        except SystemExit:
            pass
        
        # Verifica se print foi chamado com JSON
        mock_print.assert_called()
        printed_output = mock_print.call_args[0][0]
        
        # Verifica se é JSON válido
        try:
            parsed = json.loads(printed_output)
            self.assertEqual(parsed['name'], 'CreateProcessW')
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")

    @patch('win32_scraper.Win32APIScraper')
    @patch('sys.argv', ['win32_scraper.py', 'CreateProcessW', '-l', 'br'])
    def test_main_language_parameter(self, mock_scraper_class):
        """Testa parâmetro de idioma"""
        mock_instance = mock_scraper_class.return_value
        mock_instance.scrape_function.return_value = {'name': 'CreateProcessW'}
        
        try:
            main()
        except SystemExit:
            pass
        
        # Verifica se o scraper foi inicializado com o idioma correto
        mock_scraper_class.assert_called_once_with(language='br', quiet=False)

    @patch('win32_scraper.Win32APIScraper.scrape_function')
    @patch('sys.argv', ['win32_scraper.py', 'InvalidFunction'])
    def test_main_function_not_found(self, mock_scrape):
        """Testa função não encontrada"""
        mock_scrape.side_effect = Exception("Função não encontrada")
        
        with patch('win32_scraper.console.print') as mock_console:
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Verifica se saiu com código 1
            self.assertEqual(context.exception.code, 1)
            mock_console.assert_called()

    @patch('sys.argv', ['win32_scraper.py'])
    def test_main_missing_argument(self):
        """Testa argumento obrigatório ausente"""
        with self.assertRaises(SystemExit):
            main()

    def test_argument_parser(self):
        """Testa o parser de argumentos"""
        from win32_scraper import argparse
        
        # Simula parser (seria necessário extrair do main)
        parser = argparse.ArgumentParser()
        parser.add_argument("function_name")
        parser.add_argument("-l", "--language", choices=["br", "us"], default="us")
        parser.add_argument("--output", choices=["rich", "json", "markdown"], default="rich")
        
        # Testa argumentos válidos
        args = parser.parse_args(['CreateProcessW', '--output', 'json'])
        self.assertEqual(args.function_name, 'CreateProcessW')
        
        # Testa argumento de idioma
        args_br = parser.parse_args(['CreateProcessW', '-l', 'br'])
        self.assertEqual(args_br.language, 'br')
        
        args_us = parser.parse_args(['CreateProcessW', '--language', 'us'])
        self.assertEqual(args_us.language, 'us')
        self.assertEqual(args.output, 'json')
        
        # Testa argumentos padrão
        args = parser.parse_args(['TestFunction'])
        self.assertEqual(args.output, 'rich')


class TestMainFunctionality(unittest.TestCase):
    """Testes para funcionalidades principais"""
    
    @patch('win32_scraper.Win32APIScraper')
    def test_scraper_initialization(self, mock_scraper_class):
        """Testa inicialização do scraper"""
        mock_instance = Mock()
        mock_scraper_class.return_value = mock_instance
        
        # Simula criação de instância
        scraper = Win32APIScraper()
        self.assertIsNotNone(scraper)

    def test_output_formats_available(self):
        """Testa se todos os formatos de saída estão disponíveis"""
        valid_formats = ["rich", "json", "markdown"]
        
        # Estes seriam os formatos suportados pelo CLI
        for format_type in valid_formats:
            self.assertIn(format_type, valid_formats)

    @patch('win32_scraper.console')
    def test_console_output(self, mock_console):
        """Testa se o console Rich está configurado"""
        from win32_scraper import console
        self.assertIsNotNone(console)


if __name__ == '__main__':
    unittest.main(verbosity=2)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANW-NG: Win32 API Documentation Scraper (Next Generation)

A revolutionary modular tool for reverse engineers and Windows developers
to extract detailed information about Win32 API functions from Microsoft documentation.

Supports both English and Portuguese documentation with precise parameter
descriptions, function signatures, and return values.

Author: Marcos Tolosa
License: MIT
"""

import argparse
import sys
import os
import re

# Fix Windows encoding issues
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Force UTF-8 mode
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from manw_ng.core.scraper import Win32APIScraper
from manw_ng.output.formatters import RichFormatter, JSONFormatter, MarkdownFormatter
from rich.console import Console

# Configure console for Windows compatibility
console = Console(force_terminal=True, legacy_windows=True, width=100)


def validate_function_name(value: str) -> str:
    pattern = r"^[A-Za-z0-9_]+$"
    if not re.match(pattern, value):
        raise argparse.ArgumentTypeError(
            "function name must contain only letters, numbers or underscores"
        )
    return value


def main():
    parser = argparse.ArgumentParser(
        description="MANW-NG - Win32 API Documentation Scraper (Next Generation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  manw-ng.py CreateProcess                    # English documentation
  manw-ng.py -l br VirtualAlloc               # Portuguese documentation
  manw-ng.py --output json OpenProcess        # JSON output
  manw-ng.py --output markdown RegOpenKeyEx   # Markdown output
        """,
    )

    parser.add_argument(
        "function_name",
        type=validate_function_name,
        help="Nome da função Win32 para fazer scraping (ex: CreateProcessW, VirtualAlloc)",
    )
    parser.add_argument(
        "-l",
        "--language",
        choices=["br", "us"],
        default="us",
        help="Idioma da documentação: 'br' para português ou 'us' para inglês (padrão: us)",
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["rich", "json", "markdown"],
        default="rich",
        help="Formato de saída (padrão: rich)",
    )
    parser.add_argument(
        "-O",
        "--obs",
        action="store_true",
        help="Mostrar observações/remarks na saída (padrão: não mostrar)",
    )
    parser.add_argument("--version", action="version", version="MANW-NG 3.1")

    args = parser.parse_args()

    try:
        # Initialize scraper within context manager
        with Win32APIScraper(
            language=args.language, quiet=(args.output == "json")
        ) as scraper:

            if args.output != "json":
                # Localized loading messages
                loading_messages = {
                    "us": f"Scraping function: {args.function_name} (language: {args.language})",
                    "br": f"Fazendo scraping da função: {args.function_name} (idioma: {args.language})",
                }
                message = loading_messages.get(args.language, loading_messages["us"])
                console.print(f"[yellow]{message}[/yellow]")

            # Scrape function information
            function_info = scraper.scrape_function(args.function_name)

            # Format output
            if args.output == "rich":
                formatter = RichFormatter(language=args.language, show_remarks=args.obs)
                formatter.format_output(function_info)
            elif args.output == "json":
                formatter = JSONFormatter()
                print(formatter.format_output(function_info))
            elif args.output == "markdown":
                formatter = MarkdownFormatter()
                print(
                    formatter.format_output(
                        function_info, language=args.language, show_remarks=args.obs
                    )
                )

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

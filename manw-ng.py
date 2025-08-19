#!/usr/bin/env python3
"""
MANW-NG: Win32 API Documentation Scraper (Next Generation)

A revolutionary modular tool for reverse engineers and Windows developers
to extract detailed information about Win32 API functions from Microsoft documentation.

Supports both English and Portuguese documentation with precise parameter
descriptions, function signatures, and return values.

Author: Marcos
License: MIT
"""

import argparse
import sys
from manw_ng.core.scraper import Win32APIScraper
from manw_ng.output.formatters import RichFormatter, JSONFormatter, MarkdownFormatter
from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="MANW-NG - Win32 API Documentation Scraper (Next Generation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  manw-ng.py CreateProcess              # English documentation
  manw-ng.py -l br VirtualAlloc         # Portuguese documentation  
  manw-ng.py --output json OpenProcess  # JSON output
  manw-ng.py --output markdown RegOpenKeyEx  # Markdown output
        """,
    )

    parser.add_argument(
        "function_name",
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
        "--output",
        choices=["rich", "json", "markdown"],
        default="rich",
        help="Formato de saída (padrão: rich)",
    )
    parser.add_argument("--version", action="version", version="MANW-NG 2.0.0")

    args = parser.parse_args()

    try:
        # Initialize scraper
        scraper = Win32APIScraper(language=args.language, quiet=(args.output == "json"))

        if args.output != "json":
            console.print(
                f"[yellow]Fazendo scraping da função: {args.function_name} (idioma: {args.language})[/yellow]"
            )

        # Scrape function information
        function_info = scraper.scrape_function(args.function_name)

        # Format output
        if args.output == "rich":
            formatter = RichFormatter()
            formatter.format_output(function_info)
        elif args.output == "json":
            formatter = JSONFormatter()
            print(formatter.format_output(function_info))
        elif args.output == "markdown":
            formatter = MarkdownFormatter()
            print(formatter.format_output(function_info))

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

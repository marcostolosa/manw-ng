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
from manw_ng.utils.catalog_integration import get_catalog
from rich.console import Console

# Configure console for Windows compatibility
console = Console(force_terminal=True, legacy_windows=False, width=100)


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
        nargs="?",
        type=validate_function_name,
        help="Nome da função Win32 para fazer scraping (ex: CreateProcessW, VirtualAlloc)",
    )
    parser.add_argument(
        "--catalog-stats",
        action="store_true",
        help="Mostrar estatísticas do catálogo Win32 API",
    )
    parser.add_argument(
        "--update-catalog",
        action="store_true",
        help="Atualizar catálogo Win32 API da documentação oficial",
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
    parser.add_argument(
        "-u",
        "--user-agent",
        dest="user_agent",
        help="User-Agent personalizado para as requisições (padrão: aleatório)",
    )
    parser.add_argument("--version", action="version", version="MANW-NG 3.1")

    args = parser.parse_args()

    # Handle catalog update command
    if args.update_catalog:
        try:
            from manw_ng.utils.win32_api_crawler import Win32APICrawler
            import asyncio

            console.print("[bold cyan]🔄 Atualizando catálogo Win32 API...[/bold cyan]")
            console.print("Isso pode levar alguns minutos...")

            async def run_crawler():
                async with Win32APICrawler() as crawler:
                    await crawler.crawl_all_languages()
                    if crawler.api_entries:
                        crawler.save_results()
                        console.print(
                            f"[green]✅ Catálogo atualizado com {len(crawler.api_entries)} entradas![/green]"
                        )
                    else:
                        console.print("[red]❌ Nenhuma entrada encontrada![/red]")

            asyncio.run(run_crawler())
            return
        except Exception as e:
            console.print(f"[red]❌ Erro ao atualizar catálogo: {e}[/red]")
            sys.exit(1)

    # Handle catalog stats command
    if args.catalog_stats:
        catalog = get_catalog()
        if not catalog.is_catalog_available():
            console.print("[red]❌ Catálogo Win32 API não encontrado![/red]")
            console.print("Execute: manw-ng.py --update-catalog")
            sys.exit(1)

        stats = catalog.get_statistics()
        console.print("\n[bold cyan]📊 ESTATÍSTICAS DO CATÁLOGO WIN32 API[/bold cyan]")
        console.print("=" * 50)

        console.print(f"[green]Total de entradas:[/green] {stats['total_entries']}")
        console.print(f"[green]Funções únicas:[/green] {stats['unique_functions']}")

        console.print("\n[bold yellow]Por Tipo:[/bold yellow]")
        for entry_type, count in sorted(stats["by_type"].items()):
            console.print(f"  {entry_type}: {count}")

        console.print("\n[bold yellow]Por Idioma:[/bold yellow]")
        for lang, count in stats["by_language"].items():
            console.print(f"  {lang}: {count}")

        console.print("\n[bold yellow]Headers mais populares:[/bold yellow]")
        sorted_headers = sorted(
            stats["by_header"].items(), key=lambda x: x[1], reverse=True
        )[:10]
        for header, count in sorted_headers:
            console.print(f"  {header}: {count}")

        return

    if not args.function_name and not args.catalog_stats and not args.update_catalog:
        parser.error(
            "function_name é obrigatório (a menos que --catalog-stats seja usado)"
        )

    try:
        # Initialize scraper
        scraper = Win32APIScraper(
            language=args.language,
            quiet=(args.output == "json"),
            user_agent=args.user_agent,
        )

        if args.output != "json":
            # Localized loading messages
            loading_messages = {
                "us": f"Scraping: {args.function_name} (language: {args.language})",
                "br": f"Fazendo scraping: {args.function_name} (idioma: {args.language})",
            }
            message = loading_messages.get(args.language, loading_messages["us"])
            console.print(f"[yellow]{message}[/yellow]")

        # Auto-detect DLL for smart URL generation
        dll_map = {
            "createfile": "kernel32.dll",
            "readfile": "kernel32.dll",
            "writefile": "kernel32.dll",
            "getlogicaldrives": "kernel32.dll",
            "virtualalloc": "kernel32.dll",
            "loadlibrary": "kernel32.dll",
            "textout": "gdi32.dll",
            "bitblt": "gdi32.dll",
            "stretchblt": "gdi32.dll",
            "drawtext": "gdi32.dll",
            "regopen": "advapi32.dll",
            "regquery": "advapi32.dll",
            "regset": "advapi32.dll",
            "geteffectiverights": "advapi32.dll",
            "cryptacquire": "advapi32.dll",
            "shellexecute": "shell32.dll",
            "shgetfolder": "shell32.dll",
            "socket": "ws2_32.dll",
            "connect": "ws2_32.dll",
            "wsastartup": "ws2_32.dll",
            "internetopen": "wininet.dll",
            "httpopen": "wininet.dll",
            "messagebox": "user32.dll",
            "showwindow": "user32.dll",
            "getdc": "user32.dll",
            "certopen": "crypt32.dll",
            "certfind": "crypt32.dll",
            "timezone": "kernel32.dll",
            "dynamic": "kernel32.dll",
            "time": "kernel32.dll",
        }

        # Try to detect DLL
        func_lower = args.function_name.lower()
        detected_dll = None
        for key, dll in dll_map.items():
            if key in func_lower:
                detected_dll = dll
                break

        if detected_dll:
            scraper._current_function_dll = detected_dll

        # Scrape function information
        function_info = scraper.scrape_function(args.function_name)

        # Format output
        if args.output == "rich":
            try:
                formatter = RichFormatter(language=args.language, show_remarks=args.obs)
                formatter.format_output(function_info)
            except Exception as e:
                # Fallback para markdown se Rich falhar no Windows
                print("Rich output failed, using markdown fallback:")
                formatter = MarkdownFormatter()
                print(formatter.format_output(function_info))
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

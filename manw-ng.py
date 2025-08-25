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
import warnings


# Suppress specific aiohttp ResourceWarnings
class AiohttpWarningFilter:
    def __init__(self):
        self.original_stderr = sys.stderr

    def write(self, data):
        # Filter out aiohttp session warnings
        if isinstance(data, str):
            if any(
                phrase in data
                for phrase in [
                    "Unclosed client session",
                    "Unclosed connector",
                    "connections:",
                    "client_session:",
                    "connector:",
                ]
            ):
                return  # Don't write these messages
        self.original_stderr.write(data)

    def flush(self):
        self.original_stderr.flush()

    def __getattr__(self, name):
        return getattr(self.original_stderr, name)


# Install the filter
sys.stderr = AiohttpWarningFilter()

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
from manw_ng.utils.dll_map import detect_dll

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
        nargs="?",
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
    parser.add_argument(
        "-u",
        "--user-agent",
        dest="user_agent",
        help="User-Agent personalizado para as requisições (padrão: aleatório)",
    )
    parser.add_argument("--version", action="version", version="MANW-NG 3.2.0")

    args = parser.parse_args()

    if not args.function_name:
        parser.error("function_name é obrigatório")

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
        detected_dll = detect_dll(args.function_name)
        if detected_dll:
            scraper.set_current_function_dll(detected_dll)

        # Scrape function information
        function_info = scraper.scrape_function(args.function_name)

        # Explicitly close HTTP client to prevent session leaks
        try:
            if hasattr(scraper, "http_client"):
                scraper.http_client.cleanup_sync()
        except Exception:
            pass

        # Format output
        if args.output == "rich":
            try:
                formatter = RichFormatter(language=args.language, show_remarks=args.obs)
                formatter.format_output(function_info)
            except (UnicodeEncodeError, UnicodeError) as e:
                # Fallback específico para problemas de Unicode no Windows
                print("Unicode encoding error, using markdown fallback:")
                formatter = MarkdownFormatter()
                print(formatter.format_output(function_info, language=args.language))
            except Exception as e:
                # Outros erros - debug
                console.print(f"[red]Rich formatter error: {e}[/red]")
                formatter = MarkdownFormatter()
                print(formatter.format_output(function_info, language=args.language))
        elif args.output == "json":
            formatter = JSONFormatter()
            print(formatter.format_output(function_info, show_remarks=args.obs))
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
    finally:
        # Force cleanup of all async resources
        try:
            import asyncio
            import gc

            # Force garbage collection
            gc.collect()
            # Close any remaining event loops
            try:
                asyncio.set_event_loop_policy(None)
            except:
                pass
        except Exception:
            pass


if __name__ == "__main__":
    main()

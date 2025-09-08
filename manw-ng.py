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

# Suppress sklearn warnings before any other imports
import argparse
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
try:
    from sklearn.exceptions import InconsistentVersionWarning

    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except ImportError:
    pass

import sys
import os
import re


# Minimal setup for fast startup

# Fix Windows encoding issues
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Force UTF-8 mode
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Lazy imports for fast startup


def validate_function_name(value: str) -> str:
    pattern = r"^[A-Za-z0-9_\-]+$"
    if not re.match(pattern, value):
        raise argparse.ArgumentTypeError(
            "function name must contain only letters, numbers, underscores or hyphens"
        )
    return value


def main():
    # Ultra-fast exec mode bypass
    if len(sys.argv) > 1 and sys.argv[1] == "exec":
        return handle_exec_fast()

    # Lazy import argparse only for documentation mode
    import argparse

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
        help="Nome da função Windows para fazer scraping (ex: CreateProcessW, VirtualAlloc)",
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
    parser.add_argument(
        "-t",
        "--tabs",
        action="store_true",
        help="Mostrar tabelas de valores dos parâmetros (padrão: não mostrar)",
    )
    parser.add_argument("--version", action="version", version="MANW-NG 3.3.1")

    args = parser.parse_args()

    if not args.function_name:
        parser.error("function_name é obrigatório")

    try:
        # Lazy imports for documentation mode
        from manw_ng.core.scraper import Win32APIScraper
        from manw_ng.output.formatters import (
            RichFormatter,
            JSONFormatter,
            MarkdownFormatter,
        )
        from rich.console import Console
        from manw_ng.utils.dll_map import detect_dll

        # Configure console
        console = Console(force_terminal=True, legacy_windows=True, width=120)

        # Initialize scraper
        scraper = Win32APIScraper(
            language=args.language,
            quiet=(args.output == "json"),
            user_agent=args.user_agent,
        )

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

        # Check if function was found and set appropriate exit code
        function_found = function_info.get("documentation_found", False)

        # Format output
        if args.output == "rich":
            try:
                formatter = RichFormatter(
                    language=args.language,
                    show_remarks=args.obs,
                    show_parameter_tables=args.tabs,
                )
                formatter.format_output(function_info)
            except (UnicodeEncodeError, UnicodeError) as e:
                # Fallback específico para problemas de Unicode no Windows
                print("Unicode encoding error, using markdown fallback:")
                formatter = MarkdownFormatter()
                print(formatter.format_output(function_info, language=args.language))
            except Exception as e:
                # Outros erros - fallback silencioso para markdown
                try:
                    formatter = MarkdownFormatter()
                    print(
                        formatter.format_output(function_info, language=args.language)
                    )
                except Exception:
                    # Último recurso - JSON simples
                    json_formatter = JSONFormatter()
                    print(json_formatter.format_output(function_info))
        elif args.output == "json":
            formatter = JSONFormatter()
            print(
                formatter.format_output(
                    function_info,
                    show_remarks=args.obs,
                    show_parameter_tables=args.tabs,
                )
            )
        elif args.output == "markdown":
            formatter = MarkdownFormatter()
            print(
                formatter.format_output(
                    function_info,
                    language=args.language,
                    show_remarks=args.obs,
                    show_parameter_tables=args.tabs,
                )
            )

        # Exit with appropriate code
        if not function_found:
            sys.exit(1)  # Function not found

    except Exception as e:
        try:
            console.print(f"[red]Erro: {e}[/red]")
        except Exception:
            # Fallback if even console.print fails
            print(f"Error: {e}")
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


def handle_exec_fast():
    """Ultra-fast WinAPI execution"""
    if len(sys.argv) < 3:
        print("Usage: manw-ng.py exec dll:function [args...]")
        sys.exit(1)

    dll_func = sys.argv[2]
    args = sys.argv[3:]

    if ":" not in dll_func and "!" not in dll_func:
        print("Error: Use dll:function format")
        sys.exit(1)

    if ":" in dll_func:
        dll_name, func_name = dll_func.split(":", 1)
    else:
        dll_name, func_name = dll_func.split("!", 1)

    import ctypes as ct
    from ctypes import wintypes as wt

    abbrevs = {
        "k": "kernel32.dll",
        "u": "user32.dll",
        "n": "ntdll.dll",
        "a32": "advapi32.dll",
    }
    resolved_dll = abbrevs.get(
        dll_name.lower(), dll_name if "." in dll_name else f"{dll_name}.dll"
    )

    try:
        dll = ct.WinDLL(resolved_dll, use_last_error=True)

        # Find function with variants
        func = None
        resolved_name = func_name
        for variant in [func_name, func_name + "W", func_name + "A"]:
            try:
                func = getattr(dll, variant)
                resolved_name = variant
                break
            except AttributeError:
                continue

        if not func:
            print(f"Function {func_name} not found in {resolved_dll}")
            sys.exit(1)

        # Parse args
        parsed_args = []
        for arg in args:
            if arg.startswith("--"):
                break
            try:
                val = int(arg, 0)
                parsed_args.append(
                    ct.c_uint32(val) if val <= 0xFFFFFFFF else ct.c_uint64(val)
                )
            except ValueError:
                parsed_args.append(wt.LPCWSTR(arg))

        # Execute
        import time

        start = time.time()
        result = func(*parsed_args)

        print(f"✓ {resolved_dll}!{resolved_name}")
        print(f"Return: {result}")
        print(f"Executed in {time.time() - start:.3f}s")

    except Exception as e:
        print(f"✗ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

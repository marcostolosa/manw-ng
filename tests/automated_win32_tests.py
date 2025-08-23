"""
Sistema de Testes Automatizados MANW-NG
=======================================

Executa testes abrangentes em todas as funções Win32 do database,
com reporting detalhado e integração com webhook Discord.
"""

import sys
import os
import time
import json
import asyncio
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests_mock

    REQUESTS_MOCK_AVAILABLE = True
except ImportError:
    REQUESTS_MOCK_AVAILABLE = False

# Adicionar path do MANW-NG para importação
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from win32_functions_database import (
    WIN32_FUNCTIONS_DB,
    Win32Function,
    TestStatus,
    get_all_functions,
    get_functions_by_priority,
    get_statistics,
)
from manw_ng.core.scraper import Win32APIScraper
from manw_ng.monitoring.discord_webhook import DiscordWebhook
from manw_ng.utils.complete_win32_api_mapping import get_function_url


class Win32TestRunner:
    """Executor de testes automatizados para todas as funções Win32"""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        language: str = "us",
        quiet: bool = True,
        offline: bool = False,
        fixtures_dir: Optional[Path] = None,
    ):
        self.scraper = Win32APIScraper(language=language, quiet=quiet)
        self.webhook = DiscordWebhook(webhook_url) if webhook_url else None
        self.language = language
        self.quiet = quiet
        self.offline = offline
        self.fixtures_dir = fixtures_dir or Path(__file__).parent / "fixtures"
        self._offline_mock = None
        self._offline_map = {}
        if self.offline:
            self._setup_offline_mode()

        # Debug webhook configuration
        if webhook_url:
            print(
                f"🔗 Webhook configurado: {webhook_url[:50]}..."
                if len(webhook_url) > 50
                else f"🔗 Webhook configurado: {webhook_url}"
            )
        else:
            print("⚠️ Webhook não configurado - relatórios só serão salvos localmente")
        self.test_start_time = None
        self.results = {
            "total_tested": 0,
            "passed": 0,
            "failed": 0,
            "documentation_not_found": 0,
            "parser_errors": 0,
            "skipped": 0,
            "test_duration": 0,
            "functions_by_status": {},
            "detailed_results": [],
        }

    def _setup_offline_mode(self) -> None:
        """Configura mocks para execução offline usando fixtures."""
        if not REQUESTS_MOCK_AVAILABLE:
            print("⚠️ requests_mock não disponível - modo offline desabilitado")
            self.offline = False
            return

        self._offline_mock = requests_mock.Mocker()
        self._offline_mock.start()
        if not self.fixtures_dir.exists():
            return
        for fixture in self.fixtures_dir.glob("*.html"):
            func_name = fixture.stem.lower()
            url = get_function_url(func_name, self.scraper.base_url)
            if not url:
                continue
            self._offline_mock.get(url, text=fixture.read_text())
            self._offline_map[func_name] = url
        print(f"📚 Modo offline habilitado com {len(self._offline_map)} fixtures")

    def get_comprehensive_test_functions(
        self, max_functions: int = 100
    ) -> List[Win32Function]:
        """Retorna conjunto abrangente de funções para teste com máxima cobertura de DLLs e tipos"""
        all_functions = get_all_functions()

        # Funções críticas conhecidas que devem existir (prioridade máxima)
        # Agora incluindo Native API que funcionam com o novo sistema ULTRA-RÁPIDO!
        critical_functions = [
            # Native API functions (now supported!)
            "NtAllocateVirtualMemory",
            "NtFreeVirtualMemory",
            "NtQueryInformationProcess",
            "NtCreateFile",
            "ZwCreateFile",
            "ZwOpenKey",
            "RtlInitUnicodeString",
            # Win32 API functions
            "CreateFileA",
            "CreateFileW",
            "ReadFile",
            "WriteFile",
            "VirtualAlloc",
            "VirtualFree",
            "HeapCreate",
            "CreateProcessA",
            "CreateProcessW",
            "GetCurrentProcess",
            "RegOpenKeyExA",
            "RegOpenKeyExW",
            "RegQueryValueExA",
            "LoadLibraryA",
            "LoadLibraryW",
            "GetProcAddress",
            "FreeLibrary",
            # Graphics functions that should work now
            "TextOutA",
            "TextOutW",
            "BitBlt",
            "StretchBlt",
            "DrawTextA",
            "DrawTextW",
            "GetDC",
            "ReleaseDC",
            "CreatePen",
            "SelectObject",
            # Crypto functions
            "CryptAcquireContextA",
            "CertOpenSystemStoreA",
            "CertFindCertificateInStore",
            "BCryptOpenAlgorithmProvider",
            # Network functions
            "socket",
            "connect",
            "bind",
            "listen",
            "InternetOpenA",
            "InternetConnectA",
            # System functions
            "GetLogicalDrives",
            "GetSystemInfo",
            "GetVersionExA",
            # Shell functions
            "ShellExecuteA",
            "ShellExecuteExA",
            "SHGetFolderPathA",
        ]

        # Mapear DLLs para garantir cobertura equilibrada
        dll_coverage = {}
        selected_functions = []

        # Primeiro, adicionar funções críticas
        for func_name in critical_functions:
            if len(selected_functions) >= max_functions:
                break
            func = next(
                (f for f in all_functions if f.name.lower() == func_name.lower()), None
            )
            if func:
                selected_functions.append(func)
                dll = func.dll.lower() if func.dll else "unknown"
                dll_coverage[dll] = dll_coverage.get(dll, 0) + 1

        # Depois, adicionar funções de diferentes DLLs para máxima cobertura
        remaining_functions = [f for f in all_functions if f not in selected_functions]

        # Ordenar por DLL para distribuir melhor
        from collections import defaultdict

        functions_by_dll = defaultdict(list)
        for func in remaining_functions:
            dll = func.dll.lower() if func.dll else "unknown"
            functions_by_dll[dll].append(func)

        # Adicionar funções distribuindo por DLL
        dll_keys = list(functions_by_dll.keys())
        dll_index = 0

        while len(selected_functions) < max_functions and any(
            functions_by_dll.values()
        ):
            current_dll = dll_keys[dll_index % len(dll_keys)]

            if functions_by_dll[current_dll]:
                func = functions_by_dll[current_dll].pop(0)
                selected_functions.append(func)
                dll_coverage[current_dll] = dll_coverage.get(current_dll, 0) + 1

            dll_index += 1

            # Limpar DLLs vazias
            dll_keys = [dll for dll in dll_keys if functions_by_dll[dll]]
            if not dll_keys:
                break

        if not self.quiet:
            print(f"📊 Cobertura de DLLs para {len(selected_functions)} funções:")
            for dll, count in sorted(dll_coverage.items()):
                percentage = (count / len(selected_functions)) * 100
                print(f"  {dll}: {count} funções ({percentage:.1f}%)")

        return selected_functions[:max_functions]

    def get_failed_and_diverse_functions(
        self, min_functions: int = 50
    ) -> List[Win32Function]:
        """Retorna funções que falharam anteriormente + amostra diversa de headers"""
        all_functions = get_all_functions()
        selected = []

        # Funções conhecidas que falharam anteriormente
        known_failed = [
            "TextOutW",
            "StretchBlt",
            "GetLogicalDrives",
            "CertOpenSystemStore",
            "NetUserEnum",
            "ShellExecuteExA",
            "BitBlt",
            "DrawText",
            "GetDC",
            "CryptAcquireContext",
            "LoadLibraryA",
            "GetProcAddress",
            "VirtualAlloc",
            "CreateProcess",
            "RegOpenKeyEx",
            "InternetOpenA",
            "socket",
            "connect",
        ]

        # Adicionar funções que falharam
        for func_name in known_failed:
            if len(selected) >= min_functions // 2:  # Metade para failed functions
                break
            func = next(
                (f for f in all_functions if f.name.lower() == func_name.lower()), None
            )
            if func:
                selected.append(func)

        # Funções aleatórias de headers diversos para teste de cobertura
        import random

        diverse_headers_funcs = {
            "wingdi": ["CreatePen", "GetPixel", "SetPixel", "Rectangle"],
            "fileapi": ["FindFirstFile", "CopyFile", "DeleteFile", "MoveFile"],
            "memoryapi": ["VirtualProtect", "VirtualFree", "GlobalAlloc"],
            "processthreadsapi": ["TerminateProcess", "SuspendThread", "ResumeThread"],
            "winreg": ["RegCreateKey", "RegDeleteKey", "RegSetValueEx"],
            "winsock2": ["bind", "listen", "accept", "send", "recv"],
            "wincrypt": ["CryptCreateHash", "CryptEncrypt", "CryptDecrypt"],
            "shellapi": ["SHGetFolderPath", "SHFileOperation", "ShellExecute"],
            "wininet": ["InternetConnect", "HttpOpenRequest", "InternetReadFile"],
            "consoleapi": ["GetConsoleTitle", "SetConsoleTitle", "AllocConsole"],
            "libloaderapi": ["FreeLibrary", "GetModuleHandle", "GetModuleFileName"],
            "synchapi": ["CreateMutex", "WaitForSingleObject", "ReleaseMutex"],
            "errhandlingapi": ["GetLastError", "SetLastError", "FormatMessage"],
            "securitybaseapi": ["OpenProcessToken", "GetTokenInformation"],
            "winsvc": ["StartService", "StopService", "ControlService"],
            "psapi": ["GetProcessMemoryInfo", "EnumProcesses", "GetModuleBaseName"],
        }

        # Selecionar 2 funções de cada header aleatoriamente
        remaining_slots = min_functions - len(selected)
        headers_list = list(diverse_headers_funcs.keys())
        random.shuffle(headers_list)

        funcs_per_header = max(2, remaining_slots // len(headers_list))

        for header in headers_list:
            if len(selected) >= min_functions:
                break

            header_funcs = diverse_headers_funcs[header]
            random.shuffle(header_funcs)

            added_from_header = 0
            for func_name in header_funcs:
                if (
                    added_from_header >= funcs_per_header
                    or len(selected) >= min_functions
                ):
                    break

                func = next(
                    (f for f in all_functions if f.name.lower() == func_name.lower()),
                    None,
                )
                if func and func not in selected:
                    selected.append(func)
                    added_from_header += 1

        if not self.quiet:
            print(f"🎯 Selecionadas {len(selected)} funções:")
            print(
                f"  - {sum(1 for f in selected if f.name in known_failed)} funções que falharam anteriormente"
            )
            print(
                f"  - {len(selected) - sum(1 for f in selected if f.name in known_failed)} funções de headers diversos"
            )

        return selected

    async def run_failed_and_diverse_tests(
        self, min_functions: int = 50, max_concurrent: int = 5
    ) -> Dict:
        """
        Executa testes focados nas funções que falharam + amostra diversa de headers
        """
        print(f"🎯 Iniciando testes focados em funções que falharam + headers diversos")

        # Selecionar funções para teste
        test_functions = self.get_failed_and_diverse_functions(min_functions)

        if not test_functions:
            return {"error": "Nenhuma função encontrada para teste"}

        print(f"📋 Testando {len(test_functions)} funções selecionadas...")
        self.test_start_time = time.time()

        # Reset results
        self.results = {
            "total_tested": 0,
            "passed": 0,
            "failed": 0,
            "documentation_not_found": 0,
            "parser_errors": 0,
            "skipped": 0,
            "test_duration": 0,
            "functions_by_status": {},
            "detailed_results": [],
        }

        # Executar testes em lotes concorrentes
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all tasks
            future_to_function = {
                executor.submit(self._test_single_function, func, 30): func
                for func in test_functions
            }

            # Process completed tasks
            for future in as_completed(future_to_function):
                function = future_to_function[future]
                try:
                    result = future.result()
                    self._process_single_test_result(result, function)
                except Exception as e:
                    print(f"❌ Erro ao testar {function.name}: {str(e)}")
                    self.results["failed"] += 1
                    self.results["total_tested"] += 1

        # Calcular duração total
        self.results["test_duration"] = time.time() - self.test_start_time

        # Gerar relatório
        report = await self._generate_final_report()

        # Enviar via webhook se configurado
        if self.webhook:
            await self._send_webhook_report(report)

        # Salvar relatório em arquivo
        self._save_report_to_file(report)

        return report

    async def run_comprehensive_tests(
        self,
        priorities: List[str] = None,
        dlls: List[str] = None,
        max_concurrent: int = 5,
        timeout_per_function: int = 30,
    ) -> Dict:
        """
        Executa testes abrangentes nas funções Win32

        Args:
            priorities: Lista de prioridades a testar ['critical', 'high', 'medium', 'low']
            dlls: Lista de DLLs específicas para testar
            max_concurrent: Máximo de testes simultâneos
            timeout_per_function: Timeout por função em segundos
        """
        self.test_start_time = datetime.now()

        print(f"🚀 Iniciando testes abrangentes Win32 MANW-NG")
        print(f"⏰ {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Selecionar funções para teste
        functions_to_test = self._select_functions_for_test(priorities, dlls)
        total_functions = len(functions_to_test)

        print(f"📊 Testando {total_functions} funções Win32")

        if self.webhook:
            print("📡 Enviando mensagem de início via webhook...")
            success = await self.webhook.send_message(
                title="🧪 Testes Win32 Iniciados",
                description=f"Testando {total_functions} funções Win32",
                color=0x00FF00,
                fields=[
                    {
                        "name": "Prioridades",
                        "value": str(priorities or "Todas"),
                        "inline": True,
                    },
                    {"name": "DLLs", "value": str(dlls or "Todas"), "inline": True},
                    {
                        "name": "Concorrência",
                        "value": str(max_concurrent),
                        "inline": True,
                    },
                ],
            )
            print(
                f"✅ Webhook enviado com sucesso"
                if success
                else "❌ Falha ao enviar webhook"
            )

        # Executar testes com controle de concorrência
        test_results = await self._run_concurrent_tests(
            functions_to_test, max_concurrent, timeout_per_function
        )

        # Processar resultados
        self._process_test_results(test_results)

        # Gerar relatório final
        report = await self._generate_final_report()

        if self.offline and self._offline_mock:
            self._offline_mock.stop()

        return report

    def _select_functions_for_test(
        self, priorities: List[str] = None, dlls: List[str] = None
    ) -> List[Win32Function]:
        """Seleciona funções baseado nos critérios especificados"""
        all_functions = get_all_functions()

        # Filtrar por prioridade se especificado
        if priorities:
            all_functions = [f for f in all_functions if f.priority in priorities]

        # Filtrar por DLL se especificado
        if dlls:
            dll_filters = [dll.lower() for dll in dlls]
            all_functions = [
                f
                for f in all_functions
                if any(dll_filter in f.dll.lower() for dll_filter in dll_filters)
            ]

        if self.offline:
            all_functions = [
                f for f in all_functions if f.name.lower() in self._offline_map
            ]

        return all_functions

    async def _run_concurrent_tests(
        self,
        functions: List[Win32Function],
        max_concurrent: int,
        timeout_per_function: int,
    ) -> List[Dict]:
        """Executa testes com controle de concorrência"""
        results = []

        # Usar ThreadPoolExecutor para I/O bound tasks (network requests)
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all tasks
            future_to_function = {
                executor.submit(
                    self._test_single_function, func, timeout_per_function
                ): func
                for func in functions
            }

            # Process results as they complete
            completed = 0
            for future in as_completed(future_to_function):
                function = future_to_function[future]
                completed += 1

                try:
                    result = future.result()
                    results.append(result)

                    # Progress reporting
                    if completed % 10 == 0 or completed == len(functions):
                        progress = (completed / len(functions)) * 100
                        print(
                            f"📈 Progresso: {completed}/{len(functions)} ({progress:.1f}%)"
                        )

                        if self.webhook and completed % 50 == 0:
                            await self.webhook.send_message(
                                title="📊 Progresso dos Testes",
                                description=f"Testadas {completed}/{len(functions)} funções ({progress:.1f}%)",
                                color=0x0099FF,
                            )

                except Exception as e:
                    # Handle individual test failures
                    error_result = {
                        "function": function.name,
                        "status": TestStatus.PARSER_ERROR,
                        "error": str(e),
                        "duration": 0,
                        "details": {},
                    }
                    results.append(error_result)
                    print(f"❌ Erro testando {function.name}: {e}")

        return results

    def _test_single_function(self, function: Win32Function, timeout: int) -> Dict:
        """Testa uma única função Win32"""
        start_time = time.time()

        try:
            # Pass DLL info to scraper for intelligent URL generation
            self.scraper._current_function_dll = function.dll

            # Reutilizar o scraper existente para melhor performance e consistência
            result = self.scraper.scrape_function(function.name)

            duration = time.time() - start_time

            # Debug apenas em caso de falha e em ambiente CI/CD
            if not result.get("documentation_found", False) and (
                os.getenv("CI") or os.getenv("GITHUB_ACTIONS")
            ):
                print(f"❌ {function.name}: documentação não encontrada")
                if result.get("url"):
                    print(f"   URL: {result.get('url')}")

            # Determinar status do teste
            if result.get("documentation_found", False):
                if self._validate_function_result(result, function):
                    status = TestStatus.PASSED
                else:
                    status = TestStatus.PARSER_ERROR
            else:
                status = TestStatus.DOCUMENTATION_NOT_FOUND

            return {
                "function": function.name,
                "status": status,
                "duration": duration,
                "dll": function.dll,
                "header": function.header,
                "priority": function.priority,
                "details": {
                    "parameters_count": result.get("parameter_count", 0),
                    "has_signature": bool(result.get("signature")),
                    "has_description": bool(result.get("description")),
                    "has_return_description": bool(result.get("return_description")),
                    "has_remarks": bool(result.get("remarks")),
                    "documentation_language": result.get("documentation_language"),
                    "url": result.get("url"),
                },
                "error": None,
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "function": function.name,
                "status": TestStatus.PARSER_ERROR,
                "duration": duration,
                "dll": function.dll,
                "header": function.header,
                "priority": function.priority,
                "details": {},
                "error": str(e),
            }

    def _validate_function_result(self, result: Dict, function: Win32Function) -> bool:
        """Valida se o resultado do scraping está correto"""
        required_fields = ["name", "signature", "description"]

        # Verificar campos obrigatórios
        for field in required_fields:
            if not result.get(field):
                return False

        # Verificar se o nome da função está correto
        if function.name.lower() not in result.get("name", "").lower():
            return False

        # Para funções críticas, exigir mais validação
        if function.priority == "critical":
            if not result.get("parameters") and not result.get("members"):
                return False

        return True

    def _process_test_results(self, test_results: List[Dict]) -> None:
        """Processa e organiza os resultados dos testes"""
        for result in test_results:
            status = result["status"]

            # Atualizar contadores
            self.results["total_tested"] += 1

            if status == TestStatus.PASSED:
                self.results["passed"] += 1
            elif status == TestStatus.FAILED:
                self.results["failed"] += 1
            elif status == TestStatus.DOCUMENTATION_NOT_FOUND:
                self.results["documentation_not_found"] += 1
            elif status == TestStatus.PARSER_ERROR:
                self.results["parser_errors"] += 1

            # Organizar por status
            status_key = status.value
            if status_key not in self.results["functions_by_status"]:
                self.results["functions_by_status"][status_key] = []

            self.results["functions_by_status"][status_key].append(
                {
                    "name": result["function"],
                    "dll": result["dll"],
                    "header": result["header"],
                    "priority": result["priority"],
                    "duration": result["duration"],
                    "error": result.get("error"),
                    "details": result.get("details", {}),
                }
            )

        # Adicionar resultados detalhados
        self.results["detailed_results"] = test_results

        # Calcular duração total
        if self.test_start_time:
            self.results["test_duration"] = (
                datetime.now() - self.test_start_time
            ).total_seconds()

    async def _generate_final_report(self) -> Dict:
        """Gera relatório final dos testes"""
        total = self.results["total_tested"]
        passed = self.results["passed"]

        success_rate = (passed / total * 100) if total > 0 else 0

        # Estatísticas por DLL
        dll_stats = {}
        for result in self.results["detailed_results"]:
            dll = result["dll"]
            if dll not in dll_stats:
                dll_stats[dll] = {"total": 0, "passed": 0}

            dll_stats[dll]["total"] += 1
            if result["status"] == TestStatus.PASSED:
                dll_stats[dll]["passed"] += 1

        # Estatísticas por prioridade
        priority_stats = {}
        for result in self.results["detailed_results"]:
            priority = result["priority"]
            if priority not in priority_stats:
                priority_stats[priority] = {"total": 0, "passed": 0}

            priority_stats[priority]["total"] += 1
            if result["status"] == TestStatus.PASSED:
                priority_stats[priority]["passed"] += 1

        # Funções com maior tempo de resposta
        slowest_functions = sorted(
            self.results["detailed_results"], key=lambda x: x["duration"], reverse=True
        )[:10]

        report = {
            "summary": {
                "total_tested": total,
                "passed": passed,
                "failed": self.results["failed"],
                "documentation_not_found": self.results["documentation_not_found"],
                "parser_errors": self.results["parser_errors"],
                "success_rate": success_rate,
                "test_duration": self.results["test_duration"],
                "timestamp": datetime.now().isoformat(),
            },
            "by_dll": dll_stats,
            "by_priority": priority_stats,
            "slowest_functions": slowest_functions,
            "failed_functions": self.results["functions_by_status"].get("failed", []),
            "documentation_not_found": self.results["functions_by_status"].get(
                "documentation_not_found", []
            ),
            "parser_errors": self.results["functions_by_status"].get(
                "parser_error", []
            ),
        }

        # Enviar relatório via webhook com debug detalhado
        if self.webhook and self.webhook.webhook_url:
            print("📡 Enviando relatório final via webhook...")
            print(f"   - URL: {self.webhook.webhook_url[:50]}...")
            try:
                await self._send_webhook_report(report)
            except Exception as e:
                print(f"❌ Erro ao enviar webhook: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("⚠️ Webhook não disponível - relatório final não enviado")
            if self.webhook:
                print(f"   - Webhook object exists: True")
                print(f"   - Webhook URL exists: {bool(self.webhook.webhook_url)}")
            else:
                print(f"   - Webhook object: None")

        # Salvar relatório em arquivo
        self._save_report_to_file(report)

        return report

    async def _send_webhook_report(self, report: Dict) -> None:
        """Envia relatório final via Discord webhook"""
        summary = report["summary"]

        # Determinar cor baseada na taxa de sucesso
        if summary["success_rate"] >= 90:
            color = 0x00FF00  # Verde
        elif summary["success_rate"] >= 70:
            color = 0xFFFF00  # Amarelo
        else:
            color = 0xFF0000  # Vermelho

        # Preparar campos do embed
        fields = [
            {
                "name": "✅ Sucessos",
                "value": f"{summary['passed']}/{summary['total_tested']} ({summary['success_rate']:.1f}%)",
                "inline": True,
            },
            {"name": "❌ Falhas", "value": str(summary["failed"]), "inline": True},
            {
                "name": "📖 Documentação Não Encontrada",
                "value": str(summary["documentation_not_found"]),
                "inline": True,
            },
            {
                "name": "⚠️ Erros de Parser",
                "value": str(summary["parser_errors"]),
                "inline": True,
            },
            {
                "name": "⏱️ Duração Total",
                "value": f"{summary['test_duration']:.1f}s",
                "inline": True,
            },
            {"name": "🕐 Timestamp", "value": summary["timestamp"], "inline": True},
        ]

        # Adicionar top DLLs por performance
        top_dlls = sorted(
            report["by_dll"].items(),
            key=lambda x: (x[1]["passed"] / x[1]["total"]) if x[1]["total"] > 0 else 0,
            reverse=True,
        )[:5]

        if top_dlls:
            dll_info = []
            for dll, stats in top_dlls:
                rate = (
                    (stats["passed"] / stats["total"] * 100)
                    if stats["total"] > 0
                    else 0
                )
                dll_info.append(
                    f"{dll}: {stats['passed']}/{stats['total']} ({rate:.1f}%)"
                )

            fields.append(
                {"name": "📊 Top 5 DLLs", "value": "\n".join(dll_info), "inline": False}
            )

        # Adicionar funções mais lentas
        slowest_funcs = report.get("slowest_functions", [])[:5]
        if slowest_funcs:
            slowest_info = []
            for func in slowest_funcs:
                duration = func.get("duration", 0)
                name = func.get("function", "Unknown")
                dll = func.get("dll", "unknown.dll")
                slowest_info.append(f"{name} ({dll}): {duration:.1f}s")

            fields.append(
                {
                    "name": "🐌 Top 5 Mais Lentas",
                    "value": "\n".join(slowest_info),
                    "inline": False,
                }
            )

        # Adicionar estatísticas por prioridade
        priority_info = []
        for priority, stats in report.get("by_priority", {}).items():
            rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            priority_info.append(
                f"{priority.title()}: {stats['passed']}/{stats['total']} ({rate:.1f}%)"
            )

        if priority_info:
            fields.append(
                {
                    "name": "📈 Por Prioridade",
                    "value": "\n".join(priority_info),
                    "inline": False,
                }
            )

        success = await self.webhook.send_message(
            title="🎯 Relatório Final - Testes Win32 MANW-NG",
            description=f"Execução completa dos testes automatizados",
            color=color,
            fields=fields,
        )
        print(
            f"✅ Relatório principal enviado"
            if success
            else "❌ Falha ao enviar relatório principal"
        )

        # Se houver muitas falhas, enviar detalhes
        if (
            summary["failed"] > 0
            or summary["parser_errors"] > 0
            or summary["documentation_not_found"] > 0
        ):
            failed_funcs = report.get("failed_functions", [])
            error_funcs = report.get("parser_errors", [])
            not_found_funcs = report.get("documentation_not_found", [])

            # Enviar relatório de falhas se houver
            if failed_funcs:
                failed_details = []
                for i, func in enumerate(failed_funcs[:20], 1):  # Top 20 falhas
                    failed_details.append(
                        f"{i}. **{func['name']}** ({func['dll']}) - {func.get('priority', 'unknown')} priority"
                    )

                await self.webhook.send_message(
                    title="❌ Funções com Falha de Teste",
                    description=f"Encontradas {len(failed_funcs)} funções que falharam nos testes:",
                    color=0xFF0000,
                    fields=[
                        {
                            "name": f"Lista de Falhas ({len(failed_funcs)} total)",
                            "value": (
                                "\n".join(failed_details[:20])
                                if failed_details
                                else "Nenhuma falha encontrada"
                            ),
                            "inline": False,
                        }
                    ]
                    + (
                        [
                            {
                                "name": "Funções Adicionais",
                                "value": f"... e mais {len(failed_funcs) - 20} funções falharam",
                                "inline": False,
                            }
                        ]
                        if len(failed_funcs) > 20
                        else []
                    ),
                )

            # Enviar relatório de erros de parser
            if error_funcs:
                parser_details = []
                for i, func in enumerate(error_funcs[:20], 1):
                    error_msg = func.get("error", "Unknown error") or "Unknown error"
                    error_msg = error_msg[:100] if len(error_msg) > 100 else error_msg
                    parser_details.append(
                        f"{i}. **{func['name']}** ({func['dll']}) - {error_msg}"
                    )

                await self.webhook.send_message(
                    title="⚠️ Funções com Erro de Parser",
                    description=f"Encontradas {len(error_funcs)} funções com erros de parsing:",
                    color=0xFF6600,
                    fields=[
                        {
                            "name": f"Lista de Erros ({len(error_funcs)} total)",
                            "value": (
                                "\n".join(parser_details[:20])
                                if parser_details
                                else "Nenhum erro encontrado"
                            ),
                            "inline": False,
                        }
                    ]
                    + (
                        [
                            {
                                "name": "Erros Adicionais",
                                "value": f"... e mais {len(error_funcs) - 20} funções com erro",
                                "inline": False,
                            }
                        ]
                        if len(error_funcs) > 20
                        else []
                    ),
                )

            # Enviar relatório de documentação não encontrada
            if not_found_funcs:
                not_found_details = []
                for i, func in enumerate(not_found_funcs[:25], 1):  # Top 25
                    not_found_details.append(
                        f"{i}. **{func['name']}** ({func['dll']}) - {func.get('priority', 'unknown')} priority"
                    )

                await self.webhook.send_message(
                    title="📖 Funções Sem Documentação",
                    description=f"Encontradas {len(not_found_funcs)} funções sem documentação disponível:",
                    color=0xFFAA00,
                    fields=[
                        {
                            "name": f"Lista Sem Documentação ({len(not_found_funcs)} total)",
                            "value": (
                                "\n".join(not_found_details[:25])
                                if not_found_details
                                else "Todas com documentação"
                            ),
                            "inline": False,
                        }
                    ]
                    + (
                        [
                            {
                                "name": "Funções Adicionais",
                                "value": f"... e mais {len(not_found_funcs) - 25} funções sem documentação",
                                "inline": False,
                            }
                        ]
                        if len(not_found_funcs) > 25
                        else []
                    ),
                )

    def _save_report_to_file(self, report: Dict) -> None:
        """Salva relatório detalhado em arquivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"win32_tests_report_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), "reports", filename)

        # Criar diretório se não existir
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"📄 Relatório salvo em: {filepath}")


async def main():
    """Função principal para execução dos testes"""
    import argparse

    parser = argparse.ArgumentParser(description="Sistema de Testes Win32 MANW-NG")
    parser.add_argument("--webhook", help="URL do webhook Discord")
    parser.add_argument(
        "--language", choices=["us", "br"], default="us", help="Idioma dos testes"
    )
    parser.add_argument(
        "--priorities",
        nargs="+",
        choices=["critical", "high", "medium", "low"],
        help="Prioridades para testar",
    )
    parser.add_argument("--dlls", nargs="+", help="DLLs específicas para testar")
    parser.add_argument("--concurrent", type=int, default=5, help="Testes simultâneos")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout por função")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Executa testes usando fixtures offline",
    )
    parser.add_argument(
        "--test-failed",
        action="store_true",
        help="Testa funções que falharam + headers diversos (pelo menos 50 funções)",
    )
    parser.add_argument(
        "--min-functions",
        type=int,
        default=50,
        help="Número mínimo de funções para teste focado",
    )

    args = parser.parse_args()

    # Detectar webhook das variáveis de ambiente ou argumentos
    webhook_url = args.webhook or os.environ.get("DISCORD_WEBHOOK")

    # Criar runner
    runner = Win32TestRunner(
        webhook_url=webhook_url,
        language=args.language,
        quiet=args.quiet,
        offline=args.offline,
    )

    try:
        # Escolher tipo de teste
        if args.test_failed:
            print(
                "🎯 Executando teste focado em funções que falharam + headers diversos"
            )
            report = await runner.run_failed_and_diverse_tests(
                min_functions=args.min_functions, max_concurrent=args.concurrent
            )
        else:
            # Teste abrangente normal
            report = await runner.run_comprehensive_tests(
                priorities=args.priorities,
                dlls=args.dlls,
                max_concurrent=args.concurrent,
                timeout_per_function=args.timeout,
            )

        # Imprimir resumo
        print("\n" + "=" * 60)
        print("🎯 RESUMO FINAL DOS TESTES")
        print("=" * 60)
        print(f"Total testado: {report['summary']['total_tested']}")
        print(
            f"Sucessos: {report['summary']['passed']} ({report['summary']['success_rate']:.1f}%)"
        )
        print(f"Falhas: {report['summary']['failed']}")
        print(f"Sem documentação: {report['summary']['documentation_not_found']}")
        print(f"Erros de parser: {report['summary']['parser_errors']}")
        print(f"Duração: {report['summary']['test_duration']:.1f}s")
        print("=" * 60)

        # Exit code baseado no sucesso - mais tolerante para CI/CD
        exit_code = 0 if report["summary"]["success_rate"] >= 50 else 1
        return exit_code

    except Exception as e:
        print(f"❌ Erro fatal durante os testes: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Executar testes
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

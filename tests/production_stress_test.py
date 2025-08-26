#!/usr/bin/env python3

import time
import random
import statistics
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from manw_ng.core.scraper import Win32APIScraper


class ProductionStressTest:
    """
    Comprehensive production stress testing for manw-ng system
    """

    def __init__(self):
        self.test_results = {}
        self.performance_metrics = []

        # MASSIVE test function database organized by complexity and category
        self.test_functions = {
            # TIER 1: Critical System Functions (Must Work)
            "critical_system": [
                "CreateFile",
                "ReadFile",
                "WriteFile",
                "CloseHandle",
                "VirtualAlloc",
                "VirtualFree",
                "CreateProcess",
                "OpenProcess",
                "CreateThread",
                "LoadLibrary",
                "GetProcAddress",
                "MessageBox",
                "CreateWindow",
                "ShowWindow",
                "GetDC",
                "BitBlt",
                "RegOpenKey",
                "RegQueryValue",
                "InternetOpen",
                "HttpOpenRequest",
                "WSAStartup",
                "socket",
            ],
            # TIER 2: Advanced System Functions + Native APIs
            "advanced_system": [
                "CreateFileMapping",
                "MapViewOfFile",
                "UnmapViewOfFile",
                "VirtualProtect",
                "SetWindowsHookEx",
                "CallNextHookEx",
                "UnhookWindowsHookEx",
                "CreateRemoteThread",
                "WriteProcessMemory",
                "ReadProcessMemory",
                "VirtualAllocEx",
                "CreateToolhelp32Snapshot",
                "Process32First",
                "Process32Next",
                "Module32First",
                "Module32Next",
                "Thread32First",
                "CreateMutex",
                "CreateSemaphore",
                "CreateEvent",
                "WaitForMultipleObjects",
                # Native APIs - Documentadas
                "NtCreateFile",
                "ZwCreateFile",
                "NtAllocateVirtualMemory",
                "ZwAllocateVirtualMemory",
                "NtUnmapViewOfSection",
                "ZwUnmapViewOfSection",
                "NtClose",
                "ZwClose",
                "NtQueryInformationProcess",
                "NtCreateEvent",
                "ZwCreateEvent",
                "NtCreateKey",
                "ZwOpenKey",
                "NtWaitForSingleObject",
                "RtlInitUnicodeString",
            ],
            # TIER 3: Network & Internet Functions
            "network_internet": [
                "InternetConnect",
                "InternetReadFile",
                "InternetWriteFile",
                "HttpSendRequest",
                "HttpQueryInfo",
                "FtpOpenFile",
                "FtpGetFile",
                "FtpPutFile",
                "URLDownloadToFile",
                "WinHttpOpen",
                "WinHttpConnect",
                "WinHttpOpenRequest",
                "WinHttpSendRequest",
                "bind",
                "listen",
                "accept",
                "connect",
                "send",
                "recv",
                "WSAEventSelect",
                "select",
                "gethostbyname",
                "gethostbyaddr",
                "WSACleanup",
                "closesocket",
            ],
            # TIER 4: Graphics & UI Functions
            "graphics_ui": [
                "CreateDC",
                "CreateCompatibleDC",
                "CreateCompatibleBitmap",
                "SelectObject",
                "DeleteObject",
                "GetStockObject",
                "CreatePen",
                "CreateBrush",
                "CreateFont",
                "TextOut",
                "DrawText",
                "SetPixel",
                "GetPixel",
                "LineTo",
                "Rectangle",
                "Ellipse",
                "FindWindow",
                "FindWindowEx",
                "GetWindowText",
                "SetWindowText",
                "EnumWindows",
                "GetWindowRect",
                "SetWindowPos",
                "MoveWindow",
                "GetClassInfo",
                "RegisterClass",
            ],
            # TIER 5: Registry & Configuration
            "registry_config": [
                "RegCreateKey",
                "RegCreateKeyEx",
                "RegDeleteKey",
                "RegDeleteValue",
                "RegSetValue",
                "RegSetValueEx",
                "RegEnumKey",
                "RegEnumValue",
                "RegCloseKey",
                "RegFlushKey",
                "RegConnectRegistry",
                "RegNotifyChangeKeyValue",
                "RegQueryInfoKey",
                "GetPrivateProfileString",
                "WritePrivateProfileString",
                "GetProfileString",
            ],
            # TIER 6: Security & Cryptography
            "security_crypto": [
                "OpenProcessToken",
                "GetTokenInformation",
                "LookupPrivilegeValue",
                "AdjustTokenPrivileges",
                "LogonUser",
                "ImpersonateLoggedOnUser",
                "RevertToSelf",
                "CryptAcquireContext",
                "CryptCreateHash",
                "CryptHashData",
                "CryptGetHashParam",
                "CryptGenKey",
                "CryptImportKey",
                "CryptExportKey",
                "CryptEncrypt",
                "CryptDecrypt",
                "CryptSignHash",
                "CertOpenStore",
                "CertFindCertificateInStore",
                "CertGetCertificateChain",
            ],
            # TIER 7: Service & System Management
            "service_system": [
                "OpenSCManager",
                "CreateService",
                "OpenService",
                "StartService",
                "ControlService",
                "DeleteService",
                "QueryServiceStatus",
                "EnumServicesStatus",
                "CloseServiceHandle",
                "CreateProcess",
                "GetSystemInfo",
                "GetVersionEx",
                "GetComputerName",
                "GetUserName",
                "GetTickCount",
                "QueryPerformanceCounter",
                "QueryPerformanceFrequency",
                "GetSystemTime",
            ],
            # TIER 8: Native API Functions (High Difficulty)
            "native_api": [
                "NtCreateFile",
                "NtOpenFile",
                "NtReadFile",
                "NtWriteFile",
                "NtClose",
                "NtCreateProcess",
                "NtOpenProcess",
                "NtTerminateProcess",
                "NtCreateThread",
                "NtOpenThread",
                "NtSuspendThread",
                "NtResumeThread",
                "NtAllocateVirtualMemory",
                "NtFreeVirtualMemory",
                "NtProtectVirtualMemory",
                "NtMapViewOfSection",
                "NtUnmapViewOfSection",
                "NtCreateSection",
                "NtQueryInformationProcess",
                "NtQuerySystemInformation",
                "RtlInitUnicodeString",
                "RtlCreateUnicodeString",
                "RtlMoveMemory",
            ],
            # TIER 9: Multimedia & Device APIs
            "multimedia_device": [
                "PlaySound",
                "waveOutOpen",
                "waveOutWrite",
                "waveOutClose",
                "mciSendCommand",
                "DirectSoundCreate",
                "CreateDIBSection",
                "SetDIBitsToDevice",
                "StretchDIBits",
                "CreateIC",
                "GetDeviceCaps",
                "EnumDisplayDevices",
                "ChangeDisplaySettings",
                "SetupDiGetClassDevs",
                "SetupDiEnumDeviceInfo",
                "CreateFile",
                "DeviceIoControl",
            ],
            # TIER 10: COM & Advanced APIs
            "com_advanced": [
                "CoInitialize",
                "CoCreateInstance",
                "CoUninitialize",
                "CoGetClassObject",
                "OleInitialize",
                "OleUninitialize",
                "CreateBindCtx",
                "MkParseDisplayName",
                "SHGetDesktopFolder",
                "SHBrowseForFolder",
                "SHGetPathFromIDList",
                "ShellExecute",
                "ShellExecuteEx",
                "ExtractIcon",
                "SHFileOperation",
                "SHGetSpecialFolderPath",
            ],
            # TIER 11: Edge Cases & Rare Functions
            "edge_cases": [
                "DebugBreak",
                "IsDebuggerPresent",
                "OutputDebugString",
                "CheckRemoteDebuggerPresent",
                "GetThreadContext",
                "SetThreadContext",
                "ContinueDebugEvent",
                "WaitForDebugEvent",
                "CreateJobObject",
                "AssignProcessToJobObject",
                "QueryInformationJobObject",
                "TerminateJobObject",
                "CreateWaitableTimer",
                "SetWaitableTimer",
                "CancelWaitableTimer",
                "GetQueuedCompletionStatus",
                "PostQueuedCompletionStatus",
                "CreateIoCompletionPort",
            ],
            # TIER 12: Native APIs não-documentadas (devem falhar)
            "native_undocumented": [
                "LdrLoadDll",
                "RtlCreateUserThread",
                "NtCreateProcess",
                "ZwCreateProcess",
                "ZwWaitForMultipleObjects",
                "RtlZeroMemory",
                "RtlMoveMemory",
                "RtlCompareMemory",
            ],
        }

    def test_single_function(self, function_name, category):
        """Test a single function and measure performance"""
        start_time = time.time()

        try:
            scraper = Win32APIScraper(quiet=True)
            result = scraper.scrape_function(function_name)

            end_time = time.time()
            execution_time = end_time - start_time

            success = result is not None and result.get("documentation_found", False)
            url = result.get("url", "") if success else "NOT_FOUND"

            return {
                "function": function_name,
                "category": category,
                "success": success,
                "url": url,
                "execution_time": execution_time,
                "error": result.get("error", "") if not success else "",
            }
        except Exception as e:
            end_time = time.time()
            return {
                "function": function_name,
                "category": category,
                "success": False,
                "url": "ERROR",
                "execution_time": end_time - start_time,
                "error": str(e),
            }

    def run_category_test(
        self, category_name, functions, max_concurrent=10
    ):  # Higher default concurrency
        """Test all functions in a category with controlled concurrency"""
        print(f"\n=== TESTING {category_name.upper()} ({len(functions)} functions) ===")

        category_results = []

        with ThreadPoolExecutor(
            max_workers=max_concurrent * 2
        ) as executor:  # Double concurrency
            # Submit all tasks
            future_to_function = {
                executor.submit(self.test_single_function, func, category_name): func
                for func in functions
            }

            # Collect results as they complete
            for future in as_completed(future_to_function):
                result = future.result()
                category_results.append(result)

                status = "OK" if result["success"] else "FAIL"
                time_str = f"{result['execution_time']:.2f}s"
                print(f"  {status:<4} {result['function']:<25} ({time_str})")

                self.performance_metrics.append(result["execution_time"])

        # Category summary
        success_count = sum(1 for r in category_results if r["success"])
        success_rate = success_count / len(functions) * 100
        avg_time = statistics.mean([r["execution_time"] for r in category_results])

        print(
            f"  CATEGORY RESULT: {success_count}/{len(functions)} ({success_rate:.1f}%) - Avg: {avg_time:.2f}s"
        )

        self.test_results[category_name] = {
            "results": category_results,
            "success_count": success_count,
            "total_count": len(functions),
            "success_rate": success_rate,
            "avg_execution_time": avg_time,
        }

        return category_results

    def run_stress_test(self):
        """Run comprehensive stress test on all categories"""
        print("STARTING PRODUCTION STRESS TEST")
        print("=" * 80)

        overall_start = time.time()
        all_results = []

        # Test each category
        for category_name, functions in self.test_functions.items():
            category_results = self.run_category_test(category_name, functions)
            all_results.extend(category_results)

            # Minimal delay between categories for speed
            time.sleep(0.1)

        overall_end = time.time()
        total_time = overall_end - overall_start

        # Generate comprehensive report
        self.generate_stress_report(all_results, total_time)

        return all_results

    def generate_stress_report(self, all_results, total_time):
        """Generate comprehensive test report"""
        total_functions = len(all_results)
        total_success = sum(1 for r in all_results if r["success"])

        # Separate documented vs undocumented APIs for more accurate metrics
        documented_results = [
            r for r in all_results if r["category"] != "native_undocumented"
        ]
        undocumented_results = [
            r for r in all_results if r["category"] == "native_undocumented"
        ]

        documented_success = sum(1 for r in documented_results if r["success"])
        undocumented_success = sum(1 for r in undocumented_results if r["success"])

        overall_success_rate = (
            total_success / total_functions * 100 if total_functions > 0 else 0
        )
        documented_success_rate = (
            documented_success / len(documented_results) * 100
            if documented_results
            else 0
        )

        print("\n" + "=" * 80)
        print("PRODUCTION STRESS TEST REPORT")
        print("=" * 80)

        print(f"OVERALL RESULTS:")
        print(f"   Total Functions Tested: {total_functions}")
        print(f"   Successful: {total_success}")
        print(f"   Failed: {total_functions - total_success}")
        print(f"   Overall Success Rate: {overall_success_rate:.2f}%")
        print(f"   Total Execution Time: {total_time:.2f} seconds")
        print(f"   Average Time per Function: {total_time/total_functions:.2f}s")

        print(f"\nDOCUMENTED APIs (Real Success Rate):")
        print(f"   Documented Functions: {len(documented_results)}")
        print(f"   Documented Successful: {documented_success}")
        print(f"   Documented Success Rate: {documented_success_rate:.2f}%")

        if undocumented_results:
            print(f"\nUNDOCUMENTED APIs (Expected to Fail):")
            print(f"   Undocumented Functions: {len(undocumented_results)}")
            print(f"   Undocumented Successful: {undocumented_success}")
            print(f"   Note: These are internal APIs that should fail")

        # Performance metrics
        if self.performance_metrics:
            print(f"\nPERFORMANCE METRICS:")
            print(f"   Fastest Function: {min(self.performance_metrics):.3f}s")
            print(f"   Slowest Function: {max(self.performance_metrics):.3f}s")
            print(f"   Median Time: {statistics.median(self.performance_metrics):.3f}s")
            print(
                f"   Standard Deviation: {statistics.stdev(self.performance_metrics):.3f}s"
            )

        # Category breakdown
        print(f"\nCATEGORY BREAKDOWN:")
        for category, data in self.test_results.items():
            rate = data["success_rate"]
            count = f"{data['success_count']}/{data['total_count']}"
            avg_time = data["avg_execution_time"]

            status = "PASS" if rate >= 80 else "WARN" if rate >= 60 else "FAIL"
            print(
                f"   {status} {category:<20}: {count:>6} ({rate:5.1f}%) - {avg_time:.2f}s avg"
            )

        # Top failures
        failed_functions = [r for r in all_results if not r["success"]]
        if failed_functions:
            print(f"\nFAILED FUNCTIONS ({len(failed_functions)}):")
            for failure in failed_functions[:20]:  # Show top 20 failures
                print(
                    f"   • {failure['function']:<25} ({failure['category']}) - {failure['error'][:50]}..."
                )

        # Performance assessment
        print(f"\nPRODUCTION READINESS ASSESSMENT:")
        if overall_success_rate >= 90:
            print("   STATUS: EXCELLENT - Ready for production!")
        elif overall_success_rate >= 80:
            print("   STATUS: GOOD - Production ready with minor issues")
        elif overall_success_rate >= 70:
            print("   STATUS: ACCEPTABLE - Needs optimization")
        else:
            print("   STATUS: NEEDS WORK - Not ready for production")

        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        critical_failures = [
            r for r in failed_functions if r["category"] == "critical_system"
        ]
        if critical_failures:
            print(
                f"   • Fix {len(critical_failures)} critical system function failures"
            )

        slow_functions = [r for r in all_results if r["execution_time"] > 5.0]
        if slow_functions:
            print(f"   • Optimize {len(slow_functions)} slow functions (>5s)")

        if overall_success_rate < 85:
            print("   • Expand ML training dataset for better coverage")
            print("   • Add more URL patterns for failed functions")

        print("\n" + "=" * 80)


def main():
    """Run the production stress test"""
    import argparse

    parser = argparse.ArgumentParser(description="MANW-NG Production Stress Test")
    parser.add_argument(
        "--concurrent",
        type=int,
        default=8,
        help="Number of concurrent threads (default: 8)",
    )
    parser.add_argument(
        "--tier", type=int, choices=range(1, 13), help="Test only specific tier (1-12)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per function in seconds (default: 30)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode - test fewer functions per category",
    )

    args = parser.parse_args()

    print(f"MANW-NG Production Stress Test")
    print(f"   Concurrent threads: {args.concurrent}")
    print(f"   Timeout per function: {args.timeout}s")
    if args.tier:
        print(f"   Testing tier: {args.tier}")
    if args.fast:
        print(f"   Fast mode: ON")
    print()

    tester = ProductionStressTest()

    # Apply fast mode
    if args.fast:
        for category in tester.test_functions:
            # Keep only first 5 functions per category for speed
            tester.test_functions[category] = tester.test_functions[category][:5]

    # Apply tier filter
    if args.tier:
        tier_map = {
            1: ["critical_system"],
            2: ["advanced_system"],
            3: ["network_internet"],
            4: ["graphics_ui"],
            5: ["security_crypto"],
            6: ["registry_system"],
            7: ["file_system"],
            8: ["process_thread"],
            9: ["memory_management"],
            10: ["com_advanced"],
            11: ["edge_cases"],
            12: ["native_undocumented"],
        }
        selected_categories = tier_map.get(args.tier, [])
        tester.test_functions = {
            k: v for k, v in tester.test_functions.items() if k in selected_categories
        }

    tester.run_stress_test()


if __name__ == "__main__":
    main()

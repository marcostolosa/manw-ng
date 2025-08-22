"""
Database completo de funções Win32 para testes automatizados
===========================================================

Contém todas as funções Win32 conhecidas organizadas por header,
com metadados para verificação automática de cobertura.
"""

from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    NOT_TESTED = "not_tested"
    PASSED = "passed" 
    FAILED = "failed"
    DOCUMENTATION_NOT_FOUND = "doc_not_found"
    PARSER_ERROR = "parser_error"


@dataclass
class Win32Function:
    name: str
    header: str
    dll: str
    module: str
    description: str
    priority: str  # critical, high, medium, low
    test_status: TestStatus = TestStatus.NOT_TESTED
    last_test_time: str = ""
    error_details: str = ""


# Database completo organizado por header
WIN32_FUNCTIONS_DB = {
    "kernel32": {
        "fileapi.h": [
            Win32Function("CreateFileA", "fileapi.h", "kernel32.dll", "fileapi", "Creates or opens file/device", "critical"),
            Win32Function("CreateFileW", "fileapi.h", "kernel32.dll", "fileapi", "Creates or opens file/device (Unicode)", "critical"),
            Win32Function("ReadFile", "fileapi.h", "kernel32.dll", "fileapi", "Reads data from file", "critical"),
            Win32Function("WriteFile", "fileapi.h", "kernel32.dll", "fileapi", "Writes data to file", "critical"),
            Win32Function("DeleteFileA", "fileapi.h", "kernel32.dll", "fileapi", "Deletes existing file", "high"),
            Win32Function("DeleteFileW", "fileapi.h", "kernel32.dll", "fileapi", "Deletes existing file (Unicode)", "high"),
            Win32Function("CopyFileA", "fileapi.h", "kernel32.dll", "fileapi", "Copies existing file", "high"),
            Win32Function("CopyFileW", "fileapi.h", "kernel32.dll", "fileapi", "Copies existing file (Unicode)", "high"),
            Win32Function("MoveFileA", "fileapi.h", "kernel32.dll", "fileapi", "Moves/renames file", "high"),
            Win32Function("MoveFileW", "fileapi.h", "kernel32.dll", "fileapi", "Moves/renames file (Unicode)", "high"),
            Win32Function("GetFileAttributesA", "fileapi.h", "kernel32.dll", "fileapi", "Gets file attributes", "medium"),
            Win32Function("SetFileAttributesA", "fileapi.h", "kernel32.dll", "fileapi", "Sets file attributes", "medium"),
            Win32Function("FindFirstFileA", "fileapi.h", "kernel32.dll", "fileapi", "Searches directory for file", "medium"),
            Win32Function("FindNextFileA", "fileapi.h", "kernel32.dll", "fileapi", "Continues file search", "medium"),
            Win32Function("FindClose", "fileapi.h", "kernel32.dll", "fileapi", "Closes search handle", "medium"),
        ],
        "memoryapi.h": [
            Win32Function("VirtualAlloc", "memoryapi.h", "kernel32.dll", "memoryapi", "Reserves/commits memory", "critical"),
            Win32Function("VirtualAllocEx", "memoryapi.h", "kernel32.dll", "memoryapi", "Reserves memory in process", "critical"),
            Win32Function("VirtualFree", "memoryapi.h", "kernel32.dll", "memoryapi", "Releases memory pages", "critical"),
            Win32Function("VirtualProtect", "memoryapi.h", "kernel32.dll", "memoryapi", "Changes memory protection", "high"),
            Win32Function("VirtualQuery", "memoryapi.h", "kernel32.dll", "memoryapi", "Gets memory info", "medium"),
            Win32Function("ReadProcessMemory", "memoryapi.h", "kernel32.dll", "memoryapi", "Reads memory from process", "high"),
            Win32Function("WriteProcessMemory", "memoryapi.h", "kernel32.dll", "memoryapi", "Writes memory to process", "high"),
        ],
        "processthreadsapi.h": [
            Win32Function("CreateProcessA", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Creates new process", "critical"),
            Win32Function("CreateProcessW", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Creates new process (Unicode)", "critical"),
            Win32Function("OpenProcess", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Opens existing process", "critical"),
            Win32Function("TerminateProcess", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Terminates process", "high"),
            Win32Function("GetExitCodeProcess", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Gets process exit code", "medium"),
            Win32Function("CreateThread", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Creates thread", "high"),
            Win32Function("CreateRemoteThread", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Creates thread in process", "high"),
            Win32Function("SuspendThread", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Suspends thread execution", "medium"),
            Win32Function("ResumeThread", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Resumes thread execution", "medium"),
            Win32Function("GetCurrentProcess", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Gets current process handle", "medium"),
            Win32Function("GetCurrentThread", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Gets current thread handle", "medium"),
            Win32Function("GetProcessId", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Gets process ID", "medium"),
            Win32Function("GetThreadId", "processthreadsapi.h", "kernel32.dll", "processthreadsapi", "Gets thread ID", "medium"),
        ],
        "heapapi.h": [
            Win32Function("HeapCreate", "heapapi.h", "kernel32.dll", "heapapi", "Creates private heap", "medium"),
            Win32Function("HeapDestroy", "heapapi.h", "kernel32.dll", "heapapi", "Destroys heap", "medium"),
            Win32Function("HeapAlloc", "heapapi.h", "kernel32.dll", "heapapi", "Allocates memory from heap", "high"),
            Win32Function("HeapFree", "heapapi.h", "kernel32.dll", "heapapi", "Frees memory from heap", "high"),
            Win32Function("HeapReAlloc", "heapapi.h", "kernel32.dll", "heapapi", "Reallocates heap memory", "medium"),
            Win32Function("GetProcessHeap", "heapapi.h", "kernel32.dll", "heapapi", "Gets process default heap", "medium"),
        ],
        "libloaderapi.h": [
            Win32Function("LoadLibraryA", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Loads DLL module", "critical"),
            Win32Function("LoadLibraryW", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Loads DLL module (Unicode)", "critical"),
            Win32Function("LoadLibraryExA", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Loads DLL with options", "high"),
            Win32Function("LoadLibraryExW", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Loads DLL with options (Unicode)", "high"),
            Win32Function("FreeLibrary", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Frees loaded DLL", "high"),
            Win32Function("GetProcAddress", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Gets function address", "critical"),
            Win32Function("GetModuleHandleA", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Gets module handle", "medium"),
            Win32Function("GetModuleHandleW", "libloaderapi.h", "kernel32.dll", "libloaderapi", "Gets module handle (Unicode)", "medium"),
        ],
        "synchapi.h": [
            Win32Function("CreateMutexA", "synchapi.h", "kernel32.dll", "synchapi", "Creates mutex object", "medium"),
            Win32Function("CreateEventA", "synchapi.h", "kernel32.dll", "synchapi", "Creates event object", "medium"),
            Win32Function("WaitForSingleObject", "synchapi.h", "kernel32.dll", "synchapi", "Waits for object", "high"),
            Win32Function("WaitForMultipleObjects", "synchapi.h", "kernel32.dll", "synchapi", "Waits for multiple objects", "high"),
            Win32Function("ReleaseMutex", "synchapi.h", "kernel32.dll", "synchapi", "Releases mutex", "medium"),
            Win32Function("SetEvent", "synchapi.h", "kernel32.dll", "synchapi", "Sets event object", "medium"),
            Win32Function("ResetEvent", "synchapi.h", "kernel32.dll", "synchapi", "Resets event object", "medium"),
        ],
    },
    
    "user32": {
        "winuser.h": [
            Win32Function("MessageBoxA", "winuser.h", "user32.dll", "winuser", "Displays message box", "critical"),
            Win32Function("MessageBoxW", "winuser.h", "user32.dll", "winuser", "Displays message box (Unicode)", "critical"),
            Win32Function("CreateWindowA", "winuser.h", "user32.dll", "winuser", "Creates window", "critical"),
            Win32Function("CreateWindowW", "winuser.h", "user32.dll", "winuser", "Creates window (Unicode)", "critical"),
            Win32Function("CreateWindowExA", "winuser.h", "user32.dll", "winuser", "Creates window with extended style", "critical"),
            Win32Function("CreateWindowExW", "winuser.h", "user32.dll", "winuser", "Creates window with extended style (Unicode)", "critical"),
            Win32Function("DestroyWindow", "winuser.h", "user32.dll", "winuser", "Destroys window", "high"),
            Win32Function("ShowWindow", "winuser.h", "user32.dll", "winuser", "Shows/hides window", "high"),
            Win32Function("UpdateWindow", "winuser.h", "user32.dll", "winuser", "Updates window", "medium"),
            Win32Function("FindWindowA", "winuser.h", "user32.dll", "winuser", "Finds window by class/name", "high"),
            Win32Function("FindWindowW", "winuser.h", "user32.dll", "winuser", "Finds window by class/name (Unicode)", "high"),
            Win32Function("GetWindowTextA", "winuser.h", "user32.dll", "winuser", "Gets window text", "medium"),
            Win32Function("SetWindowTextA", "winuser.h", "user32.dll", "winuser", "Sets window text", "medium"),
            Win32Function("SendMessageA", "winuser.h", "user32.dll", "winuser", "Sends message to window", "high"),
            Win32Function("SendMessageW", "winuser.h", "user32.dll", "winuser", "Sends message to window (Unicode)", "high"),
            Win32Function("PostMessageA", "winuser.h", "user32.dll", "winuser", "Posts message to queue", "high"),
            Win32Function("PostMessageW", "winuser.h", "user32.dll", "winuser", "Posts message to queue (Unicode)", "high"),
            Win32Function("GetMessage", "winuser.h", "user32.dll", "winuser", "Gets message from queue", "high"),
            Win32Function("PeekMessage", "winuser.h", "user32.dll", "winuser", "Checks message queue", "medium"),
            Win32Function("DispatchMessage", "winuser.h", "user32.dll", "winuser", "Dispatches message", "high"),
            Win32Function("RegisterClassA", "winuser.h", "user32.dll", "winuser", "Registers window class", "high"),
            Win32Function("RegisterClassW", "winuser.h", "user32.dll", "winuser", "Registers window class (Unicode)", "high"),
            Win32Function("UnregisterClass", "winuser.h", "user32.dll", "winuser", "Unregisters window class", "medium"),
            Win32Function("DefWindowProcA", "winuser.h", "user32.dll", "winuser", "Default window procedure", "high"),
            Win32Function("DefWindowProcW", "winuser.h", "user32.dll", "winuser", "Default window procedure (Unicode)", "high"),
            Win32Function("SetWindowsHookExA", "winuser.h", "user32.dll", "winuser", "Installs hook procedure", "high"),
            Win32Function("SetWindowsHookExW", "winuser.h", "user32.dll", "winuser", "Installs hook procedure (Unicode)", "high"),
            Win32Function("UnhookWindowsHookEx", "winuser.h", "user32.dll", "winuser", "Removes hook procedure", "medium"),
            Win32Function("CallNextHookEx", "winuser.h", "user32.dll", "winuser", "Calls next hook", "medium"),
            Win32Function("MessageBeep", "winuser.h", "user32.dll", "winuser", "Plays system sound", "low"),
            Win32Function("InvalidateRect", "winuser.h", "user32.dll", "winuser", "Invalidates window region", "medium"),
            Win32Function("GetDC", "winuser.h", "user32.dll", "winuser", "Gets device context", "medium"),
            Win32Function("ReleaseDC", "winuser.h", "user32.dll", "winuser", "Releases device context", "medium"),
        ],
    },
    
    "wininet": {
        "wininet.h": [
            Win32Function("InternetOpenA", "wininet.h", "wininet.dll", "wininet", "Initializes WinINet", "critical"),
            Win32Function("InternetOpenW", "wininet.h", "wininet.dll", "wininet", "Initializes WinINet (Unicode)", "critical"),
            Win32Function("InternetConnectA", "wininet.h", "wininet.dll", "wininet", "Opens Internet connection", "high"),
            Win32Function("InternetConnectW", "wininet.h", "wininet.dll", "wininet", "Opens Internet connection (Unicode)", "high"),
            Win32Function("InternetCloseHandle", "wininet.h", "wininet.dll", "wininet", "Closes Internet handle", "high"),
            Win32Function("HttpOpenRequestA", "wininet.h", "wininet.dll", "wininet", "Creates HTTP request", "high"),
            Win32Function("HttpOpenRequestW", "wininet.h", "wininet.dll", "wininet", "Creates HTTP request (Unicode)", "high"),
            Win32Function("HttpSendRequestA", "wininet.h", "wininet.dll", "wininet", "Sends HTTP request", "high"),
            Win32Function("HttpSendRequestW", "wininet.h", "wininet.dll", "wininet", "Sends HTTP request (Unicode)", "high"),
            Win32Function("InternetReadFile", "wininet.h", "wininet.dll", "wininet", "Reads Internet file", "high"),
            Win32Function("InternetWriteFile", "wininet.h", "wininet.dll", "wininet", "Writes Internet file", "medium"),
            Win32Function("FtpOpenFileA", "wininet.h", "wininet.dll", "wininet", "Opens FTP file", "medium"),
            Win32Function("FtpGetFileA", "wininet.h", "wininet.dll", "wininet", "Downloads FTP file", "medium"),
            Win32Function("FtpPutFileA", "wininet.h", "wininet.dll", "wininet", "Uploads FTP file", "medium"),
        ],
    },
    
    "ntdll": {
        "winternl.h": [
            Win32Function("NtQueryInformationProcess", "winternl.h", "ntdll.dll", "winternl", "Queries process information", "high"),
            Win32Function("NtQuerySystemInformation", "winternl.h", "ntdll.dll", "winternl", "Queries system information", "medium"),
            Win32Function("RtlAllocateHeap", "winternl.h", "ntdll.dll", "winternl", "Allocates heap memory", "high"),
            Win32Function("RtlFreeHeap", "winternl.h", "ntdll.dll", "winternl", "Frees heap memory", "high"),
            Win32Function("RtlCreateHeap", "winternl.h", "ntdll.dll", "winternl", "Creates heap", "medium"),
            Win32Function("RtlDestroyHeap", "winternl.h", "ntdll.dll", "winternl", "Destroys heap", "medium"),
            Win32Function("RtlZeroMemory", "winternl.h", "ntdll.dll", "winternl", "Fills memory with zeros", "medium"),
            Win32Function("RtlCopyMemory", "winternl.h", "ntdll.dll", "winternl", "Copies memory", "medium"),
            Win32Function("RtlMoveMemory", "winternl.h", "ntdll.dll", "winternl", "Moves memory", "medium"),
        ],
    },
    
    "advapi32": {
        "winreg.h": [
            Win32Function("RegOpenKeyExA", "winreg.h", "advapi32.dll", "winreg", "Opens registry key", "high"),
            Win32Function("RegOpenKeyExW", "winreg.h", "advapi32.dll", "winreg", "Opens registry key (Unicode)", "high"),
            Win32Function("RegCreateKeyExA", "winreg.h", "advapi32.dll", "winreg", "Creates registry key", "high"),
            Win32Function("RegCreateKeyExW", "winreg.h", "advapi32.dll", "winreg", "Creates registry key (Unicode)", "high"),
            Win32Function("RegDeleteKeyA", "winreg.h", "advapi32.dll", "winreg", "Deletes registry key", "medium"),
            Win32Function("RegDeleteKeyW", "winreg.h", "advapi32.dll", "winreg", "Deletes registry key (Unicode)", "medium"),
            Win32Function("RegQueryValueExA", "winreg.h", "advapi32.dll", "winreg", "Queries registry value", "high"),
            Win32Function("RegQueryValueExW", "winreg.h", "advapi32.dll", "winreg", "Queries registry value (Unicode)", "high"),
            Win32Function("RegSetValueExA", "winreg.h", "advapi32.dll", "winreg", "Sets registry value", "high"),
            Win32Function("RegSetValueExW", "winreg.h", "advapi32.dll", "winreg", "Sets registry value (Unicode)", "high"),
            Win32Function("RegCloseKey", "winreg.h", "advapi32.dll", "winreg", "Closes registry key", "high"),
            Win32Function("RegDeleteValue", "winreg.h", "advapi32.dll", "winreg", "Deletes registry value", "medium"),
        ],
        "winsvc.h": [
            Win32Function("OpenSCManagerA", "winsvc.h", "advapi32.dll", "winsvc", "Opens service manager", "medium"),
            Win32Function("OpenServiceA", "winsvc.h", "advapi32.dll", "winsvc", "Opens service", "medium"),
            Win32Function("CreateServiceA", "winsvc.h", "advapi32.dll", "winsvc", "Creates service", "medium"),
            Win32Function("StartServiceA", "winsvc.h", "advapi32.dll", "winsvc", "Starts service", "medium"),
            Win32Function("ControlService", "winsvc.h", "advapi32.dll", "winsvc", "Controls service", "medium"),
            Win32Function("DeleteService", "winsvc.h", "advapi32.dll", "winsvc", "Deletes service", "low"),
        ],
    },
    
    "ws2_32": {
        "winsock2.h": [
            Win32Function("WSAStartup", "winsock2.h", "ws2_32.dll", "winsock2", "Initializes Winsock", "critical"),
            Win32Function("WSACleanup", "winsock2.h", "ws2_32.dll", "winsock2", "Terminates Winsock", "critical"),
            Win32Function("socket", "winsock2.h", "ws2_32.dll", "winsock2", "Creates socket", "critical"),
            Win32Function("bind", "winsock2.h", "ws2_32.dll", "winsock2", "Binds socket", "high"),
            Win32Function("listen", "winsock2.h", "ws2_32.dll", "winsock2", "Listens for connections", "high"),
            Win32Function("accept", "winsock2.h", "ws2_32.dll", "winsock2", "Accepts connection", "high"),
            Win32Function("connect", "winsock2.h", "ws2_32.dll", "winsock2", "Connects to server", "high"),
            Win32Function("send", "winsock2.h", "ws2_32.dll", "winsock2", "Sends data", "high"),
            Win32Function("recv", "winsock2.h", "ws2_32.dll", "winsock2", "Receives data", "high"),
            Win32Function("closesocket", "winsock2.h", "ws2_32.dll", "winsock2", "Closes socket", "high"),
        ],
    },
}


def get_all_functions() -> List[Win32Function]:
    """Retorna lista plana de todas as funções no database"""
    functions = []
    for dll_name, headers in WIN32_FUNCTIONS_DB.items():
        for header_name, func_list in headers.items():
            functions.extend(func_list)
    return functions


def get_functions_by_priority(priority: str) -> List[Win32Function]:
    """Retorna funções filtradas por prioridade"""
    return [func for func in get_all_functions() if func.priority == priority]


def get_functions_by_dll(dll_name: str) -> List[Win32Function]:
    """Retorna funções de uma DLL específica"""
    if dll_name in WIN32_FUNCTIONS_DB:
        functions = []
        for header_name, func_list in WIN32_FUNCTIONS_DB[dll_name].items():
            functions.extend(func_list)
        return functions
    return []


def get_functions_by_header(header_name: str) -> List[Win32Function]:
    """Retorna funções de um header específico"""
    functions = []
    for dll_name, headers in WIN32_FUNCTIONS_DB.items():
        if header_name in headers:
            functions.extend(headers[header_name])
    return functions


def get_statistics() -> Dict:
    """Retorna estatísticas do database"""
    all_functions = get_all_functions()
    total = len(all_functions)
    
    by_priority = {
        "critical": len([f for f in all_functions if f.priority == "critical"]),
        "high": len([f for f in all_functions if f.priority == "high"]), 
        "medium": len([f for f in all_functions if f.priority == "medium"]),
        "low": len([f for f in all_functions if f.priority == "low"]),
    }
    
    by_dll = {}
    for dll_name in WIN32_FUNCTIONS_DB.keys():
        by_dll[dll_name] = len(get_functions_by_dll(dll_name))
    
    by_status = {
        "not_tested": len([f for f in all_functions if f.test_status == TestStatus.NOT_TESTED]),
        "passed": len([f for f in all_functions if f.test_status == TestStatus.PASSED]),
        "failed": len([f for f in all_functions if f.test_status == TestStatus.FAILED]),
        "doc_not_found": len([f for f in all_functions if f.test_status == TestStatus.DOCUMENTATION_NOT_FOUND]),
        "parser_error": len([f for f in all_functions if f.test_status == TestStatus.PARSER_ERROR]),
    }
    
    return {
        "total_functions": total,
        "by_priority": by_priority,
        "by_dll": by_dll,
        "by_status": by_status,
        "coverage_percent": round((by_status["passed"] / total * 100), 2) if total > 0 else 0,
    }


if __name__ == "__main__":
    # Test do database
    stats = get_statistics()
    print(f"Database Win32 Functions:")
    print(f"Total: {stats['total_functions']} funções")
    print(f"Por prioridade: {stats['by_priority']}")
    print(f"Por DLL: {stats['by_dll']}")
    print(f"Coverage: {stats['coverage_percent']}%")
#!/usr/bin/env python3
"""
Configuração global para pytest
"""

import pytest
import sys
import os

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def sample_html():
    """HTML de exemplo para testes"""
    return """
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


@pytest.fixture
def sample_function_info():
    """Informações de exemplo de uma função"""
    return {
        "name": "CreateProcessW",
        "dll": "Kernel32.dll",
        "calling_convention": "__stdcall",
        "parameters": [
            {
                "name": "lpApplicationName",
                "type": "LPCWSTR",
                "description": "The name of the module to be executed.",
            },
            {
                "name": "lpCommandLine",
                "type": "LPWSTR",
                "description": "The command line to be executed.",
            },
        ],
        "parameter_count": 2,
        "architectures": ["x86", "x64"],
        "signature": "BOOL CreateProcessW(...);",
        "return_type": "BOOL",
        "return_description": "If the function succeeds, the return value is nonzero.",
        "description": "Creates a new process and its primary thread.",
    }


def pytest_configure(config):
    """Configuração do pytest"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "network: mark test as requiring network")

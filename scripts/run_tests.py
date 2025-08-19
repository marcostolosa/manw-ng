#!/usr/bin/env python3
"""
Script para executar todos os testes localmente
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Executa um comando e exibe o resultado"""
    print(f"\n🔍 {description}")
    print(f"Running: {command}")
    print("-" * 50)

    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Executa todos os testes e verificações"""
    # Muda para o diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🧪 MANW-NG - Test Suite")
    print("=" * 50)

    tests = [
        ("python -m pytest tests/ -v --tb=short", "Unit Tests"),
        (
            "python -m pytest tests/ -v --cov=manw_ng --cov-report=html",
            "Coverage Report",
        ),
        ("flake8 . --count --statistics", "Code Linting"),
        (
            "python -c \"import manw_ng; print('✅ Import test passed')\"",
            "Import Test",
        ),
        ("python manw-ng.py CreateProcessW --output json", "CLI Test"),
    ]

    results = []

    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))

    # Sumário dos resultados
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{description}: {status}")

    # Verifica se todos passaram
    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

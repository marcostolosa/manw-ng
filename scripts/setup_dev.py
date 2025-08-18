#!/usr/bin/env python3
"""
Script para configurar ambiente de desenvolvimento
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Executa um comando"""
    print(f"🔄 {description}")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} - Complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e}")
        return False


def main():
    """Configura o ambiente de desenvolvimento"""
    print("🚀 Setting up Win32 API Scraper Development Environment")
    print("=" * 60)

    # Muda para o diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    setup_steps = [
        ("python -m pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing production dependencies"),
        ("pip install -r requirements-dev.txt", "Installing development dependencies"),
        (
            "python -c \"import win32_scraper; print('Import test successful')\"",
            "Testing imports",
        ),
    ]

    all_success = True

    for command, description in setup_steps:
        success = run_command(command, description)
        if not success:
            all_success = False

    # Criar diretórios necessários
    directories = ["logs", "coverage", "reports"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

    print("\n" + "=" * 60)

    if all_success:
        print("🎉 Development environment setup complete!")
        print("\n📋 Next steps:")
        print("1. Run tests: python scripts/run_tests.py")
        print("2. Start coding: python win32_scraper.py CreateProcessW")
        print("3. Format code: black .")
        print("4. Check linting: flake8 .")
        return 0
    else:
        print("❌ Setup failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

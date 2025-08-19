#!/usr/bin/env python3
"""
Script de build para criar executáveis do Win32 API Scraper
"""

import subprocess
import sys
import os
import platform


def run_command(cmd, cwd=None):
    """Execute um comando e retorna o resultado"""
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, cwd=cwd, capture_output=True, text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def main():
    print("Iniciando build do MANW-NG...")

    # Instalar dependências
    print("Instalando dependências...")
    success, output = run_command(f"{sys.executable} -m pip install --upgrade pip")
    if not success:
        print(f"Erro ao atualizar pip: {output}")
        return 1

    success, output = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    if not success:
        print(f"Erro ao instalar dependências: {output}")
        return 1

    success, output = run_command(f"{sys.executable} -m pip install pyinstaller")
    if not success:
        print(f"Erro ao instalar PyInstaller: {output}")
        return 1

    # Determinar nome do executável baseado na plataforma
    system = platform.system().lower()
    arch = platform.machine().lower()

    if "64" in arch or "amd64" in arch or "x86_64" in arch:
        arch_suffix = "x64"
    else:
        arch_suffix = "x86"

    if system == "windows":
        exe_name = f"manw-ng-windows-{arch_suffix}.exe"
    else:
        exe_name = f"manw-ng-linux-{arch_suffix}"

    print(f"Criando executável: {exe_name}")

    # Build com PyInstaller
    cmd = f"pyinstaller --clean --distpath=dist --workpath=build --name={exe_name} --onefile manw-ng.py"

    print("Executando PyInstaller...")
    success, output = run_command(cmd)
    if not success:
        print(f"❌ Erro no build: {output}")
        return 1

    # Verificar se o arquivo foi criado
    exe_path = os.path.join("dist", exe_name)
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print(f"Build concluído com sucesso!")
        print(f"Arquivo: {exe_path}")
        print(f"Tamanho: {file_size:.1f} MB")

        # Testar executável
        print("Testando executável...")
        success, output = run_command(f'"{exe_path}" --help')
        if success:
            print("Teste do executável passou!")
            print(f"Output:\n{output}")
        else:
            print(f"Teste do executável falhou: {output}")
    else:
        print(f"Executável não foi encontrado em {exe_path}")
        return 1

    print("Build do MANW-NG finalizado!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""
Test Runner Simplificado para MANW-NG
=====================================

Script simplificado para testar o sistema de testes antes da integração CI/CD.
"""

import asyncio
import sys
import os

# Adicionar path do MANW-NG para importação
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from automated_win32_tests import Win32TestRunner


async def test_critical_functions():
    """Testa apenas funções críticas rapidamente"""

    print("🧪 Testando funções críticas Win32...")

    # Criar runner sem webhook (teste local)
    runner = Win32TestRunner(webhook_url=None, language="us", quiet=True)

    try:
        # Executar testes apenas em funções críticas
        report = await runner.run_comprehensive_tests(
            priorities=["critical"],
            max_concurrent=3,  # Menor concorrência para teste
            timeout_per_function=15,  # Timeout menor
        )

        # Mostrar resultados
        print("\n" + "=" * 50)
        print("📊 RESULTADOS DO TESTE")
        print("=" * 50)

        summary = report["summary"]
        print(f"Total testado: {summary['total_tested']}")
        print(f"Sucessos: {summary['passed']} ({summary['success_rate']:.1f}%)")
        print(f"Falhas: {summary['failed']}")
        print(f"Sem documentação: {summary['documentation_not_found']}")
        print(f"Erros de parser: {summary['parser_errors']}")
        print(f"Duração: {summary['test_duration']:.1f}s")

        # Mostrar algumas funções que falharam
        failed_funcs = report.get("failed_functions", [])
        if failed_funcs:
            print(f"\n❌ Primeiras {min(5, len(failed_funcs))} funções que falharam:")
            for func in failed_funcs[:5]:
                print(f"  - {func['name']} ({func['dll']})")

        # Mostrar funções sem documentação
        no_doc_funcs = report.get("documentation_not_found", [])
        if no_doc_funcs:
            print(f"\n📖 Primeiras {min(5, len(no_doc_funcs))} sem documentação:")
            for func in no_doc_funcs[:5]:
                print(f"  - {func['name']} ({func['dll']})")

        print("=" * 50)

        return summary["success_rate"] >= 70

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_single_functions():
    """Testa funções individuais conhecidas"""

    print("\n🔍 Testando funções individuais...")

    test_functions = [
        "CreateFileA",
        "MessageBoxA",
        "InternetOpenA",
        "VirtualAlloc",
        "LoadLibraryA",
    ]

    runner = Win32TestRunner(webhook_url=None, language="us", quiet=True)

    results = {}

    for func_name in test_functions:
        print(f"  Testando {func_name}...")
        try:
            result = runner.scraper.scrape_function(func_name)

            if result.get("documentation_found", False):
                status = "✅ Sucesso"
                has_sig = "✓" if result.get("signature") else "✗"
                has_params = "✓" if result.get("parameters") else "✗"
                has_desc = "✓" if result.get("description") else "✗"
                details = f"Sig:{has_sig} Params:{has_params} Desc:{has_desc}"
                results[func_name] = f"{status} ({details})"
            else:
                results[func_name] = "❌ Não encontrada"

        except Exception as e:
            results[func_name] = f"⚠️ Erro: {str(e)[:50]}..."

    print("\n📋 Resultados individuais:")
    for func, result in results.items():
        print(f"  {func:<15}: {result}")

    success_count = sum(1 for r in results.values() if "✅" in r)
    return success_count >= len(test_functions) * 0.8  # 80% success rate


def test_database_integrity():
    """Testa integridade do database"""

    print("\n📚 Testando integridade do database...")

    try:
        from win32_functions_database import get_statistics, get_all_functions

        stats = get_statistics()
        functions = get_all_functions()

        print(f"  Total de funções: {stats['total_functions']}")
        print(f"  Por DLL: {stats['by_dll']}")
        print(f"  Por prioridade: {stats['by_priority']}")

        # Verificar se há funções com dados válidos
        valid_functions = 0
        for func in functions[:10]:  # Testar primeiras 10
            if func.name and func.dll and func.header and func.priority:
                valid_functions += 1

        print(f"  Funções válidas (amostra): {valid_functions}/10")

        return valid_functions >= 8  # 80% das amostras devem ser válidas

    except Exception as e:
        print(f"  ❌ Erro no database: {e}")
        return False


async def main():
    """Função principal de testes"""

    print("🚀 Iniciando testes do sistema MANW-NG")
    print("=" * 60)

    all_passed = True

    # Teste 1: Database
    print("\n1️⃣ TESTE DE DATABASE")
    db_ok = test_database_integrity()
    if db_ok:
        print("✅ Database OK")
    else:
        print("❌ Database falhou")
        all_passed = False

    # Teste 2: Funções individuais
    print("\n2️⃣ TESTE DE FUNÇÕES INDIVIDUAIS")
    individual_ok = await test_single_functions()
    if individual_ok:
        print("✅ Funções individuais OK")
    else:
        print("❌ Funções individuais falharam")
        all_passed = False

    # Teste 3: Sistema de testes abrangentes
    print("\n3️⃣ TESTE DO SISTEMA ABRANGENTE")
    comprehensive_ok = await test_critical_functions()
    if comprehensive_ok:
        print("✅ Sistema abrangente OK")
    else:
        print("❌ Sistema abrangente falhou")
        all_passed = False

    # Resultado final
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("Sistema pronto para integração CI/CD")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("Verificar problemas antes da integração")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

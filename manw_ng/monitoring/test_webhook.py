#!/usr/bin/env python3
"""
Teste simples para verificar webhook Discord
"""
import asyncio
import sys
import os

sys.path.insert(0, ".")

from manw_ng.monitoring.discord_webhook import DiscordWebhook


async def test_webhook(webhook_url: str):
    """Testa o webhook Discord"""
    print(f"🔧 Testando webhook: {webhook_url[:50]}...")

    try:
        # Criar webhook
        webhook = DiscordWebhook(webhook_url)

        # Enviar mensagem de teste
        success = await webhook.send_message(
            title="🧪 Teste MANW-NG",
            description="Teste de conectividade do webhook Discord",
            color=0x00FF00,
            fields=[
                {
                    "name": "Status",
                    "value": "Webhook funcionando corretamente!",
                    "inline": False,
                }
            ],
        )

        if success:
            print("✅ Webhook funcionando corretamente!")
            return True
        else:
            print("❌ Falha no envio da mensagem")
            return False

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Função principal"""
    # Verificar se URL foi fornecida
    webhook_url = None

    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    else:
        webhook_url = os.getenv("DISCORD_WEBHOOK")

    if not webhook_url:
        print("❌ URL do webhook não fornecida!")
        print("")
        print("Use uma destas formas:")
        print("1. python test_webhook.py https://discord.com/api/webhooks/...")
        print(
            "2. set DISCORD_WEBHOOK=https://discord.com/api/webhooks/... && python test_webhook.py"
        )
        return False

    # Executar teste
    result = asyncio.run(test_webhook(webhook_url))
    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

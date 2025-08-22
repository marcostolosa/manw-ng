"""
Discord Webhook Integration for MANW-NG Win32 API Monitoring
=============================================================

Provides Discord notifications for Win32 API monitoring in GitHub Actions.
Enhanced version for comprehensive test reporting and monitoring.
"""

import os
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests

# Import aiohttp optionally for async webhook support
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


@dataclass
class FunctionFailure:
    """Represents a failed function lookup"""

    name: str
    url: str
    error_code: int
    error_message: str
    timestamp: datetime


class DiscordWebhookMonitor:
    """Discord webhook integration for Win32 API monitoring"""

    def __init__(self, webhook_url: str, rate_limit: int = 10):
        """
        Initialize Discord webhook monitor

        Args:
            webhook_url: Discord webhook URL
            rate_limit: Maximum messages per hour (default: 10)
        """
        self.webhook_url = webhook_url
        self.rate_limit = rate_limit
        self.message_history = []
        self.session = requests.Session()

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Clean old messages
        self.message_history = [
            msg_time for msg_time in self.message_history if msg_time > hour_ago
        ]

        return len(self.message_history) < self.rate_limit

    def _send_webhook_message(self, embed: Dict[str, Any]) -> bool:
        """
        Send message to Discord webhook

        Args:
            embed: Discord embed object

        Returns:
            True if successful, False otherwise
        """
        if not self._check_rate_limit():
            return False

        try:
            payload = {"embeds": [embed]}

            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 204:
                self.message_history.append(datetime.now())
                return True
            else:
                return False

        except Exception:
            return False

    def send_404_alert(
        self, function_name: str, url: str, additional_context: str = ""
    ) -> bool:
        """
        Send 404 error alert to Discord

        Args:
            function_name: Name of the function that failed
            url: URL that returned 404
            additional_context: Additional error context

        Returns:
            True if sent successfully
        """
        embed = {
            "title": "Win32 API Function Not Found (404)",
            "description": f"The Win32 API function **{function_name}** returned a 404 error.",
            "color": 0xFF0000,
            "fields": [
                {
                    "name": "Function Name",
                    "value": f"`{function_name}`",
                    "inline": True,
                },
                {
                    "name": "Failed URL",
                    "value": f"[Documentation Link]({url})",
                    "inline": False,
                },
            ],
            "footer": {"text": "MANW-NG Win32 API Monitor"},
            "timestamp": datetime.now().isoformat(),
        }

        if additional_context:
            embed["fields"].append(
                {
                    "name": "Additional Context",
                    "value": additional_context[:1000],
                    "inline": False,
                }
            )

        return self._send_webhook_message(embed)

    def send_batch_failure_report(
        self, failures: List[FunctionFailure], scan_context: Optional[Dict] = None
    ) -> bool:
        """
        Send batch failure report to Discord

        Args:
            failures: List of function failures
            scan_context: Additional scan context (success rate, total tested, etc.)

        Returns:
            True if sent successfully
        """
        if not failures:
            return True

        top_failures = failures[:10]

        description = f"Found {len(failures)} failed function lookups during scan."
        if scan_context:
            success_rate = scan_context.get("success_rate", 0)
            total_tested = scan_context.get("total_tested", 0)
            description += f"\n\nScan Results:\n"
            description += f"Success Rate: {success_rate:.1f}%\n"
            description += f"Total Tested: {total_tested} functions"

        embed = {
            "title": "Win32 API Batch Failure Report",
            "description": description,
            "color": 0xFF6600,
            "fields": [],
            "footer": {"text": "MANW-NG Win32 API Monitor"},
            "timestamp": datetime.now().isoformat(),
        }

        failure_text = ""
        for i, failure in enumerate(top_failures, 1):
            failure_text += f"{i}. **{failure.name}** - HTTP {failure.error_code}\n"

        embed["fields"].append(
            {
                "name": f"Top {len(top_failures)} Failures",
                "value": failure_text[:1000],
                "inline": False,
            }
        )

        if len(failures) > 10:
            embed["fields"].append(
                {
                    "name": "Additional Failures",
                    "value": f"... and {len(failures) - 10} more functions failed",
                    "inline": False,
                }
            )

        return self._send_webhook_message(embed)

    def send_success_report(
        self, success_rate: float, total_tested: int, additional_info: str = ""
    ) -> bool:
        """
        Send success rate report to Discord

        Args:
            success_rate: Success rate percentage
            total_tested: Total number of functions tested
            additional_info: Additional information

        Returns:
            True if sent successfully
        """
        if success_rate >= 95:
            color = 0x00FF00
            status = "Excellent"
        elif success_rate >= 85:
            color = 0xFFFF00
            status = "Good"
        else:
            color = 0xFF0000
            status = "Needs Attention"

        embed = {
            "title": f"Win32 API Coverage Report",
            "description": f"**{success_rate:.1f}%** success rate ({status})",
            "color": color,
            "fields": [
                {
                    "name": "Functions Tested",
                    "value": f"{total_tested}",
                    "inline": True,
                },
                {
                    "name": "Success Rate",
                    "value": f"{success_rate:.1f}%",
                    "inline": True,
                },
                {"name": "Status", "value": f"{status}", "inline": True},
            ],
            "footer": {"text": "MANW-NG Win32 API Monitor"},
            "timestamp": datetime.now().isoformat(),
        }

        if additional_info:
            embed["fields"].append(
                {
                    "name": "Additional Information",
                    "value": additional_info[:1000],
                    "inline": False,
                }
            )

        return self._send_webhook_message(embed)

    def test_webhook(self) -> bool:
        """Test the webhook connection"""
        embed = {
            "title": "MANW-NG Webhook Test",
            "description": "Webhook connection test from MANW-NG Win32 API Monitor.",
            "color": 0x00FF00,
            "fields": [
                {
                    "name": "Status",
                    "value": "Webhook connection successful",
                    "inline": False,
                }
            ],
            "footer": {"text": "MANW-NG Win32 API Monitor - Test"},
            "timestamp": datetime.now().isoformat(),
        }

        return self._send_webhook_message(embed)


def create_webhook_monitor_from_env() -> Optional[DiscordWebhookMonitor]:
    """
    Create Discord webhook monitor from environment variables

    Returns:
        DiscordWebhookMonitor instance or None if not configured
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    if not webhook_url:
        return None

    rate_limit = int(os.getenv("DISCORD_RATE_LIMIT", "10"))

    return DiscordWebhookMonitor(webhook_url, rate_limit)


class DiscordWebhook:
    """
    Enhanced Discord webhook client for async operations
    Compatible with automated testing system
    """
    
    def __init__(self, webhook_url: Optional[str] = None, rate_limit: int = 30):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK")
        self.rate_limit = rate_limit
        self.message_history = []
        self._session = None
        self._aiohttp_available = AIOHTTP_AVAILABLE
    
    async def __aenter__(self):
        if self._aiohttp_available:
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session and self._aiohttp_available:
            await self._session.close()
    
    def _check_rate_limit(self) -> bool:
        """Check if within rate limits"""
        if not self.webhook_url:
            return False
            
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old messages
        self.message_history = [
            msg_time for msg_time in self.message_history if msg_time > hour_ago
        ]
        
        return len(self.message_history) < self.rate_limit
    
    async def send_message(
        self, 
        title: str, 
        description: str, 
        color: int = 0x0099FF,
        fields: List[Dict] = None,
        footer: str = None,
        timestamp: str = None
    ) -> bool:
        """
        Send message to Discord webhook
        
        Args:
            title: Message title
            description: Message description 
            color: Embed color (hex)
            fields: List of embed fields
            footer: Footer text
            timestamp: ISO timestamp
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url or not self._check_rate_limit() or not self._aiohttp_available:
            return False
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": footer or "MANW-NG Win32 Test System"},
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        
        if fields:
            embed["fields"] = fields[:25]  # Discord limit
        
        payload = {"embeds": [embed]}
        
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            async with self._session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 204:
                    self.message_history.append(datetime.now())
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Webhook error: {e}")
            return False
    
    async def send_test_start(self, total_functions: int, priorities: List[str] = None) -> bool:
        """Send test start notification"""
        return await self.send_message(
            title="🧪 Testes Win32 Iniciados",
            description=f"Iniciando testes em {total_functions} funções Win32",
            color=0x00FF00,
            fields=[
                {
                    "name": "Total de Funções",
                    "value": str(total_functions),
                    "inline": True
                },
                {
                    "name": "Prioridades",
                    "value": ", ".join(priorities) if priorities else "Todas",
                    "inline": True
                },
                {
                    "name": "Status",
                    "value": "Executando...",
                    "inline": True
                }
            ]
        )
    
    async def send_progress_update(self, completed: int, total: int, success_rate: float = None) -> bool:
        """Send progress update"""
        progress = (completed / total * 100) if total > 0 else 0
        
        fields = [
            {
                "name": "Progresso",
                "value": f"{completed}/{total} ({progress:.1f}%)",
                "inline": True
            }
        ]
        
        if success_rate is not None:
            fields.append({
                "name": "Taxa de Sucesso",
                "value": f"{success_rate:.1f}%",
                "inline": True
            })
        
        return await self.send_message(
            title="📊 Progresso dos Testes",
            description="Atualização do progresso dos testes Win32",
            color=0x0099FF,
            fields=fields
        )
    
    async def send_final_report(self, report_data: Dict) -> bool:
        """Send comprehensive final report"""
        summary = report_data.get("summary", {})
        
        # Determine color based on success rate
        success_rate = summary.get("success_rate", 0)
        if success_rate >= 90:
            color = 0x00FF00  # Green
        elif success_rate >= 70:
            color = 0xFFFF00  # Yellow
        else:
            color = 0xFF0000  # Red
        
        fields = [
            {
                "name": "✅ Sucessos",
                "value": f"{summary.get('passed', 0)}/{summary.get('total_tested', 0)}",
                "inline": True
            },
            {
                "name": "📈 Taxa de Sucesso",
                "value": f"{success_rate:.1f}%",
                "inline": True
            },
            {
                "name": "❌ Falhas",
                "value": str(summary.get('failed', 0)),
                "inline": True
            },
            {
                "name": "📖 Sem Documentação",
                "value": str(summary.get('documentation_not_found', 0)),
                "inline": True
            },
            {
                "name": "⚠️ Erros de Parser",
                "value": str(summary.get('parser_errors', 0)),
                "inline": True
            },
            {
                "name": "⏱️ Duração",
                "value": f"{summary.get('test_duration', 0):.1f}s",
                "inline": True
            }
        ]
        
        return await self.send_message(
            title="🎯 Relatório Final - Testes Win32 MANW-NG",
            description="Execução completa dos testes automatizados Win32",
            color=color,
            fields=fields
        )
    
    async def send_error_details(self, failed_functions: List[Dict], error_functions: List[Dict]) -> bool:
        """Send detailed error information"""
        error_details = []
        
        # Add failed functions
        for func in failed_functions[:10]:
            error_details.append(f"❌ {func.get('name', 'Unknown')} ({func.get('dll', 'Unknown')})")
        
        # Add parser error functions  
        for func in error_functions[:10]:
            error_msg = func.get('error', 'Unknown error')[:50] + "..." if len(func.get('error', '')) > 50 else func.get('error', 'Unknown error')
            error_details.append(f"⚠️ {func.get('name', 'Unknown')}: {error_msg}")
        
        if error_details:
            return await self.send_message(
                title="🔍 Detalhes dos Erros",
                description="Principais falhas encontradas nos testes:",
                color=0xFF6600,
                fields=[{
                    "name": "Erros Encontrados",
                    "value": "\n".join(error_details[:15]),  # Discord field limit
                    "inline": False
                }]
            )
        
        return True

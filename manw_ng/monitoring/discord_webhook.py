"""
Discord Webhook Integration for MANW-NG Win32 API Monitoring
=============================================================

Provides Discord notifications for Win32 API monitoring in GitHub Actions.
No local testing - designed for CI/CD pipeline use only.
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests


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

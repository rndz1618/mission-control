"""Discord Tool for CrewAI - sends messages via webhook"""
import json
import os
from typing import Optional
import requests
from crewai.tools import BaseTool


class DiscordTool(BaseTool):
    name: str = "Discord Tool"
    description: str = "Send messages to Discord channel via webhook URL. Provide webhook_url or rely on DISCORD_WEBHOOK_URL env var."
    
    def _run(self, message: str, webhook_url: Optional[str] = None) -> str:
        """
        Send a message to Discord.
        Args:
            message: The content to send (max 2000 chars)
            webhook_url: Optional webhook URL; if not provided, uses DISCORD_WEBHOOK_URL environment variable.
        Returns:
            Success message or error.
        """
        url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not url:
            return "Error: No webhook URL provided. Set DISCORD_WEBHOOK_URL env var or pass webhook_url parameter."
        
        if len(message) > 2000:
            return "Error: Message exceeds Discord limit of 2000 characters."
        
        payload = {"content": message}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                return "Message sent to Discord successfully."
            else:
                return f"Error: Discord returned {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Error: Failed to send message to Discord: {str(e)}"
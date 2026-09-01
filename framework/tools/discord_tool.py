"""Discord Tool for CrewAI - sends messages via webhook"""
import json
import logging
import os
from typing import Optional
import requests
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class DiscordTool(BaseTool):
    name: str = "discord_tool"
    description: str = (
        "Send messages to a Discord channel via webhook URL. "
        "Provide: message (required, text up to 2000 characters), webhook_url (optional). "
        "Example: {\"message\": \"Hello from Mission Control!\"}"
    )

    def _run(self, message: str, webhook_url: Optional[str] = None) -> str:
        url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not url:
            err = "Error: No webhook URL provided. Set DISCORD_WEBHOOK_URL env var or pass webhook_url."
            logger.warning(err)
            return err

        if len(message) > 2000:
            err = "Error: Message exceeds Discord limit of 2000 characters."
            logger.warning(err)
            return err

        payload = {"content": message}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                logger.info("Message sent to Discord successfully.")
                return "Message sent to Discord successfully."
            else:
                err = f"Error: Discord returned {response.status_code}: {response.text}"
                logger.error(err)
                return err
        except requests.exceptions.RequestException as e:
            err = f"Error: Failed to send message to Discord: {str(e)}"
            logger.error(err)
            return err

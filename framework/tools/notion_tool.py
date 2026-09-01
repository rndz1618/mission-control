"""Notion Tools for CrewAI - wraps ntn CLI

Each action is a separate tool for proper function-calling schema.
"""
import json
import subprocess
from crewai.tools import BaseTool


class NotionSearchTool(BaseTool):
    name: str = "notion_search"
    description: str = (
        "Search pages in Notion. "
        "Provide: query (required, the search term). "
        "Example: {\"query\": \"project plan\"}"
    )

    def _run(self, query: str) -> str:
        if not query:
            return "Error: query is required."
        try:
            result = subprocess.run(
                ["ntn", "search", query],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except FileNotFoundError:
            return "Error: ntn CLI not found."
        except Exception as e:
            return f"Error: {str(e)}"


class NotionReadPageTool(BaseTool):
    name: str = "notion_read_page"
    description: str = (
        "Read the contents of a Notion page by its ID. "
        "Provide: page_id (required). "
        "Example: {\"page_id\": \"abc123-def456\"}"
    )

    def _run(self, page_id: str) -> str:
        if not page_id:
            return "Error: page_id is required."
        try:
            result = subprocess.run(
                ["ntn", "pages", "get", page_id],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except FileNotFoundError:
            return "Error: ntn CLI not found."
        except Exception as e:
            return f"Error: {str(e)}"


class NotionCreatePageTool(BaseTool):
    name: str = "notion_create_page"
    description: str = (
        "Create a new page in Notion. "
        "Provide: parent_id (required), title (required), content (optional, markdown text). "
        "Example: {\"parent_id\": \"abc123\", \"title\": \"My Page\", \"content\": \"# Hello\"}"
    )

    def _run(self, parent_id: str, title: str, content: str = "") -> str:
        if not parent_id or not title:
            return "Error: parent_id and title are required."
        try:
            cmd = ["ntn", "pages", "create", "--parent", parent_id, "--title", title]
            if content:
                cmd.extend(["--content", content])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except FileNotFoundError:
            return "Error: ntn CLI not found."
        except Exception as e:
            return f"Error: {str(e)}"


class NotionUpdatePageTool(BaseTool):
    name: str = "notion_update_page"
    description: str = (
        "Update an existing Notion page. "
        "Provide: page_id (required), content (required, the new content). "
        "Example: {\"page_id\": \"abc123\", \"content\": \"Updated content here\"}"
    )

    def _run(self, page_id: str, content: str) -> str:
        if not page_id:
            return "Error: page_id is required."
        try:
            cmd = ["ntn", "pages", "update", page_id]
            if content:
                cmd.extend(["--content", content])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except FileNotFoundError:
            return "Error: ntn CLI not found."
        except Exception as e:
            return f"Error: {str(e)}"

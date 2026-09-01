"""Notion Tools for CrewAI - wraps ntn CLI

Each action is a separate tool for proper function-calling schema.
"""
import logging
import subprocess
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class NotionSearchTool(BaseTool):
    name: str = "notion_search"
    description: str = (
        "Search pages in Notion. "
        "Provide: query (required, the search term). "
        "Example: {\"query\": \"project plan\"}"
    )

    def _run(self, query: str) -> str:
        if not query:
            err = "Error: query is required."
            logger.warning(err)
            return err
        try:
            result = subprocess.run(
                ["ntn", "pages", "list"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = "Error: ntn CLI not found."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class NotionReadPageTool(BaseTool):
    name: str = "notion_read_page"
    description: str = (
        "Read the contents of a Notion page by its ID. "
        "Provide: page_id (required). "
        "Example: {\"page_id\": \"abc123-def456\"}"
    )

    def _run(self, page_id: str) -> str:
        if not page_id:
            err = "Error: page_id is required."
            logger.warning(err)
            return err
        try:
            result = subprocess.run(
                ["ntn", "pages", "get", page_id],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = "Error: ntn CLI not found."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class NotionCreatePageTool(BaseTool):
    name: str = "notion_create_page"
    description: str = (
        "Create a new page in Notion. "
        "Provide: parent_id (required), title (required), content (optional, markdown text). "
        "Example: {\"parent_id\": \"abc123\", \"title\": \"My Page\", \"content\": \"# Hello\"}"
    )

    def _run(self, parent_id: str, title: str, content: str = "") -> str:
        if not parent_id or not title:
            err = "Error: parent_id and title are required."
            logger.warning(err)
            return err
        try:
            cmd = ["ntn", "pages", "create", "--parent", parent_id, "--title", title]
            if content:
                cmd.extend(["--content", content])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = "Error: ntn CLI not found."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class NotionUpdatePageTool(BaseTool):
    name: str = "notion_update_page"
    description: str = (
        "Update an existing Notion page. "
        "Provide: page_id (required), content (required, the new content). "
        "Example: {\"page_id\": \"abc123\", \"content\": \"Updated content here\"}"
    )

    def _run(self, page_id: str, content: str) -> str:
        if not page_id or not content:
            err = "Error: page_id and content are required."
            logger.warning(err)
            return err
        try:
            cmd = ["ntn", "pages", "update", page_id, "--content", content]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = "Error: ntn CLI not found."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err

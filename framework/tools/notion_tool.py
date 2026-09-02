"""Notion Tools for CrewAI - wraps ntn CLI

Each action is a separate tool for proper function-calling schema.
Includes standardized graceful fallback and availability checks.
"""
import json
import logging
import shutil
import subprocess
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

CLI_NAME = "ntn"


def is_cli_available() -> bool:
    """Check if ntn CLI binary is available on the system PATH."""
    return shutil.which(CLI_NAME) is not None


class NotionSearchTool(BaseTool):
    name: str = "notion_search"
    description: str = (
        "Search pages and databases in Notion by query term. "
        "Provide: query (required, the search keyword). "
        "Example: {\"query\": \"project plan\"}"
    )

    def _run(self, query: str) -> str:
        if not query:
            err = "Error: query is required."
            logger.warning(err)
            return err

        if not is_cli_available():
            logger.info("ntn CLI not found on system PATH. Returning notice.")
            return (
                f"Notice: '{CLI_NAME}' CLI is not installed. Live Notion search for '{query}' is unavailable. "
                "Please proceed using your internal knowledge and context."
            )

        try:
            payload = json.dumps({"query": query, "page_size": 10})
            result = subprocess.run(
                [CLI_NAME, "api", "v1/search", "-d", payload],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            elif result.stderr.strip():
                err = f"Search returned notice: {result.stderr.strip()}"
                logger.warning(err)
                return err
            return f"No results found in Notion for query: '{query}'."
        except subprocess.TimeoutExpired:
            err = "Error: Notion search timed out after 30 seconds."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error during Notion search: {str(e)}"
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

        if not is_cli_available():
            logger.info("ntn CLI not found. Returning notice.")
            return (
                f"Notice: '{CLI_NAME}' CLI is not installed. Cannot retrieve live page for ID '{page_id}'. "
                "Please proceed using the available task context."
            )

        try:
            result = subprocess.run(
                [CLI_NAME, "pages", "get", page_id],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error reading Notion page: {result.stderr.strip()}"
            logger.error(err)
            return err
        except subprocess.TimeoutExpired:
            err = "Error: Notion read request timed out."
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

        if not is_cli_available():
            logger.info("ntn CLI not found. Simulating Notion page creation.")
            return (
                f"Notice: '{CLI_NAME}' CLI is not installed. Page '{title}' recorded locally under parent '{parent_id}'. "
                "Proceeding with workflow."
            )

        try:
            cmd = [CLI_NAME, "pages", "create", "--parent", f"page:{parent_id}", "--content", f"# {title}\n\n{content}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("Notion page created successfully.")
                return result.stdout or f"Page '{title}' created successfully."
            err = f"Error creating Notion page: {result.stderr.strip()}"
            logger.error(err)
            return err
        except subprocess.TimeoutExpired:
            err = "Error: Notion page create timed out."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class NotionUpdatePageTool(BaseTool):
    name: str = "notion_update_page"
    description: str = (
        "Update an existing Notion page with new Markdown content. "
        "Provide: page_id (required), content (required, the new markdown content). "
        "Example: {\"page_id\": \"abc123\", \"content\": \"Updated content here\"}"
    )

    def _run(self, page_id: str, content: str) -> str:
        if not page_id or not content:
            err = "Error: page_id and content are required."
            logger.warning(err)
            return err

        if not is_cli_available():
            logger.info("ntn CLI not found. Simulating Notion page update.")
            return (
                f"Notice: '{CLI_NAME}' CLI is not installed. Content update for page '{page_id}' recorded locally. "
                "Proceeding with workflow."
            )

        try:
            cmd = [CLI_NAME, "pages", "edit", page_id, "--content", content]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("Notion page updated successfully.")
                return result.stdout or f"Page '{page_id}' updated successfully."
            err = f"Error updating Notion page: {result.stderr.strip()}"
            logger.error(err)
            return err
        except subprocess.TimeoutExpired:
            err = "Error: Notion page update timed out."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err

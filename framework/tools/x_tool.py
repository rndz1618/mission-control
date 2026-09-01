"""X/Twitter Tools for CrewAI - wraps xurl CLI

Each action is a separate tool so CrewAI's native function calling
can generate proper JSON arguments.
If xurl is not installed on the host, gracefully informs the agent
to proceed with internal reasoning.
"""
import json
import logging
import re
import shutil
import subprocess
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

CLI_NAME = "xurl"


def is_cli_available() -> bool:
    """Check if xurl CLI binary is available on the system PATH."""
    return shutil.which(CLI_NAME) is not None


class XSearchTool(BaseTool):
    name: str = "x_search"
    description: str = (
        "Search tweets on X/Twitter. "
        "Provide a JSON string with: query (required), count (optional, default 10). "
        "Example: {\"query\": \"AI trends 2026\", \"count\": 5}"
    )

    def _run(self, query: str, count: int = 10) -> str:
        if not is_cli_available():
            logger.info("xurl CLI not found on system PATH. Informing agent to proceed with internal knowledge.")
            return (
                "Notice: 'xurl' CLI is not installed on this system. Live Twitter search is currently unavailable. "
                "Please proceed using your extensive internal knowledge and analytical capabilities to identify trends."
            )

        try:
            result = subprocess.run(
                [CLI_NAME, "search", query, "--count", str(count)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            elif result.stderr.strip():
                err = f"Search completed but returned notice: {result.stderr.strip()}"
                logger.warning(err)
                return err
            else:
                return "No matching tweets found for the query."
        except subprocess.TimeoutExpired:
            err = "Notice: Live search request timed out after 30 seconds."
            logger.warning(err)
            return err
        except Exception as e:
            err = f"Error during search: {str(e)}"
            logger.exception(err)
            return err


class XPostTweetTool(BaseTool):
    name: str = "x_post_tweet"
    description: str = (
        "Post a tweet to X/Twitter. "
        "Provide: text (required, the tweet content), reply_to (optional tweet ID to reply to). "
        "Example: {\"text\": \"Hello world!\", \"reply_to\": \"123456789\"}"
    )

    def _run(self, text: str, reply_to: str = "") -> str:
        if not text:
            err = "Error: text is required to post a tweet."
            logger.warning(err)
            return err

        if not is_cli_available():
            logger.info("xurl CLI not found on system PATH. Simulating tweet post.")
            return (
                f"[SIMULATED POST] 'xurl' CLI is not installed. Tweet prepared successfully:\n\n{text}"
            )

        try:
            cmd = [CLI_NAME, "post", "--text", text]
            if reply_to:
                cmd.extend(["--reply", reply_to])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("Tweet posted successfully.")
                return result.stdout or "Tweet posted successfully."
            err = f"Error posting tweet: {result.stderr.strip()}"
            logger.error(err)
            return err
        except subprocess.TimeoutExpired:
            err = "Error: Post timed out."
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class XPostThreadTool(BaseTool):
    name: str = "x_post_thread"
    description: str = (
        "Post a thread of tweets to X/Twitter. "
        "Provide: tweets (required, a list of tweet texts as pipe-separated '|' strings or a JSON array). "
        "Example: {\"tweets\": [\"First tweet\", \"Second tweet\", \"Third tweet\"]}"
    )

    def _run(self, tweets: str) -> str:
        """tweets can be a JSON array string or pipe-separated string."""
        try:
            tweet_list = json.loads(tweets) if tweets.startswith("[") else [t.strip() for t in tweets.split("|")]
        except json.JSONDecodeError:
            tweet_list = [t.strip() for t in tweets.split("|")]

        if not tweet_list:
            err = "Error: at least one tweet is required."
            logger.warning(err)
            return err

        if not is_cli_available():
            logger.info("xurl CLI not found on system PATH. Simulating thread post.")
            formatted = "\n\n---\n".join(f"Tweet {i+1}:\n{t}" for i, t in enumerate(tweet_list))
            return f"[SIMULATED THREAD] 'xurl' CLI is not installed. Thread prepared ({len(tweet_list)} tweets):\n\n{formatted}"

        results = []
        previous_id = None
        for tweet_text in tweet_list:
            cmd = [CLI_NAME, "post", "--text", tweet_text]
            if previous_id:
                cmd.extend(["--reply", previous_id])
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    err = f"Error posting tweet in thread: {result.stderr.strip()}"
                    logger.error(err)
                    return err
                results.append(result.stdout)
                match = re.search(r'status/(\d+)', result.stdout)
                if match:
                    previous_id = match.group(1)
            except Exception as e:
                err = f"Error posting thread item: {str(e)}"
                logger.exception(err)
                return err

        logger.info("Thread posted successfully.")
        return f"Thread posted ({len(tweet_list)} tweets):\n" + "\n".join(results)


class XGetTweetTool(BaseTool):
    name: str = "x_get_tweet"
    description: str = (
        "Get details of a specific tweet by its ID. "
        "Provide: tweet_id (required). "
        "Example: {\"tweet_id\": \"1234567890\"}"
    )

    def _run(self, tweet_id: str) -> str:
        if not tweet_id:
            err = "Error: tweet_id is required."
            logger.warning(err)
            return err

        if not is_cli_available():
            return f"Notice: 'xurl' CLI is not installed. Cannot retrieve live tweet with ID: {tweet_id}."

        try:
            result = subprocess.run(
                [CLI_NAME, "get", tweet_id],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr.strip()}"
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err

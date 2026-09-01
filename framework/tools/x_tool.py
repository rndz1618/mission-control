"""X/Twitter Tools for CrewAI - wraps xurl CLI

Each action is a separate tool so CrewAI's native function calling
can generate proper JSON arguments.
"""
import re
import subprocess
from crewai.tools import BaseTool


class XSearchTool(BaseTool):
    name: str = "x_search"
    description: str = (
        "Search tweets on X/Twitter. "
        "Provide a JSON string with: query (required), count (optional, default 10). "
        "Example: {\"query\": \"AI trends 2026\", \"count\": 5}"
    )

    def _run(self, query: str, count: int = 10) -> str:
        try:
            result = subprocess.run(
                ["xurl", "search", query, "--count", str(count)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            elif result.stderr.strip():
                return f"Search completed but returned error: {result.stderr}"
            else:
                return "No results found for the query."
        except FileNotFoundError:
            return "Error: xurl CLI not found. Please ensure xurl is installed."
        except subprocess.TimeoutExpired:
            return "Error: Search timed out after 30 seconds."
        except Exception as e:
            return f"Error: {str(e)}"


class XPostTweetTool(BaseTool):
    name: str = "x_post_tweet"
    description: str = (
        "Post a tweet to X/Twitter. "
        "Provide: text (required, the tweet content), reply_to (optional tweet ID to reply to). "
        "Example: {\"text\": \"Hello world!\", \"reply_to\": \"123456789\"}"
    )

    def _run(self, text: str, reply_to: str = "") -> str:
        if not text:
            return "Error: text is required to post a tweet."
        try:
            cmd = ["xurl", "post", "--text", text]
            if reply_to:
                cmd.extend(["--reply", reply_to])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout or "Tweet posted successfully."
            return f"Error posting tweet: {result.stderr}"
        except FileNotFoundError:
            return "Error: xurl CLI not found."
        except subprocess.TimeoutExpired:
            return "Error: Post timed out."
        except Exception as e:
            return f"Error: {str(e)}"


class XPostThreadTool(BaseTool):
    name: str = "x_post_thread"
    description: str = (
        "Post a thread of tweets to X/Twitter. "
        "Provide: tweets (required, a list of tweet texts as comma-separated strings or a JSON array). "
        "Example: {\"tweets\": [\"First tweet\", \"Second tweet\", \"Third tweet\"]}"
    )

    def _run(self, tweets: str) -> str:
        """tweets can be a JSON array string or comma-separated."""
        import json
        try:
            tweet_list = json.loads(tweets) if tweets.startswith("[") else [t.strip() for t in tweets.split("|")]
        except json.JSONDecodeError:
            tweet_list = [t.strip() for t in tweets.split("|")]

        if not tweet_list:
            return "Error: at least one tweet is required."

        results = []
        previous_id = None
        for tweet_text in tweet_list:
            cmd = ["xurl", "post", "--text", tweet_text]
            if previous_id:
                cmd.extend(["--reply", previous_id])
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    return f"Error posting tweet: {result.stderr}"
                results.append(result.stdout)
                match = re.search(r'status/(\d+)', result.stdout)
                if match:
                    previous_id = match.group(1)
            except Exception as e:
                return f"Error: {str(e)}"

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
            return "Error: tweet_id is required."
        try:
            result = subprocess.run(
                ["xurl", "get", tweet_id],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except FileNotFoundError:
            return "Error: xurl CLI not found."
        except Exception as e:
            return f"Error: {str(e)}"

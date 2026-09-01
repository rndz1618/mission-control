"""Market Data Tools for CrewAI - wraps rndz-market-data ingest script

Each action is a separate tool for proper function-calling schema.
"""
import logging
import os
import subprocess
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

# Configurable path with environment variable override
DEFAULT_SCRIPT_PATH = os.getenv("MARKET_DATA_SCRIPT_PATH", os.path.expanduser("~/rndz-market-data/ingest.py"))


class MarketDataTickerTool(BaseTool):
    name: str = "market_data_ticker"
    description: str = (
        "Fetch current ticker price for a cryptocurrency symbol. "
        "Provide: symbol (required, e.g. 'BTC/USDT', 'ETH/USDT'). "
        "Example: {\"symbol\": \"BTC/USDT\"}"
    )

    def _run(self, symbol: str) -> str:
        if not symbol:
            return "Error: symbol is required."
        try:
            result = subprocess.run(
                ["python3", DEFAULT_SCRIPT_PATH, "ticker", "--symbol", symbol],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = f"Error: Script not found at {DEFAULT_SCRIPT_PATH}"
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class MarketDataOHLCVTool(BaseTool):
    name: str = "market_data_ohlcv"
    description: str = (
        "Fetch OHLCV candlestick data for a symbol. "
        "Provide: symbol (required), timeframe (optional: '1m','5m','15m','1h','4h','1d', default '1h'), limit (optional, default 50). "
        "Example: {\"symbol\": \"BTC/USDT\", \"timeframe\": \"1h\", \"limit\": 24}"
    )

    def _run(self, symbol: str, timeframe: str = "1h", limit: int = 50) -> str:
        if not symbol:
            return "Error: symbol is required."
        try:
            result = subprocess.run(
                ["python3", DEFAULT_SCRIPT_PATH, "ohlcv", "--symbol", symbol, "--timeframe", timeframe, "--limit", str(limit)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = f"Error: Script not found at {DEFAULT_SCRIPT_PATH}"
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err


class MarketDataTrendTool(BaseTool):
    name: str = "market_data_trend"
    description: str = (
        "Analyze trend indicators (SMA, EMA, RSI, MACD) for a symbol. "
        "Provide: symbol (required), timeframe (optional, default '1h'), lookback (optional, default 50). "
        "Example: {\"symbol\": \"BTC/USDT\", \"timeframe\": \"1h\", \"lookback\": 50}"
    )

    def _run(self, symbol: str, timeframe: str = "1h", lookback: int = 50) -> str:
        if not symbol:
            return "Error: symbol is required."
        try:
            result = subprocess.run(
                ["python3", DEFAULT_SCRIPT_PATH, "analyze", "--symbol", symbol, "--timeframe", timeframe, "--lookback", str(lookback)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            err = f"Error: {result.stderr}"
            logger.error(err)
            return err
        except FileNotFoundError:
            err = f"Error: Script not found at {DEFAULT_SCRIPT_PATH}"
            logger.error(err)
            return err
        except Exception as e:
            err = f"Error: {str(e)}"
            logger.exception(err)
            return err

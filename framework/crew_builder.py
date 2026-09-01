"""
CrewAI Crew Builder for Mission Control Framework
Loads mission.yaml and constructs a CrewAI crew.
"""
import logging
import os
from typing import List, Dict, Any
import yaml
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from crewai.llm import LLM

logger = logging.getLogger(__name__)

# Import individual tool classes
from framework.tools.notion_tool import (
    NotionSearchTool,
    NotionReadPageTool,
    NotionCreatePageTool,
    NotionUpdatePageTool,
)
from framework.tools.x_tool import (
    XSearchTool,
    XPostTweetTool,
    XPostThreadTool,
    XGetTweetTool,
)
from framework.tools.market_data_tool import (
    MarketDataTickerTool,
    MarketDataOHLCVTool,
    MarketDataTrendTool,
)
from framework.tools.discord_tool import DiscordTool

# Tool registry maps string names in mission.yaml to tool instances
TOOL_REGISTRY = {
    # Notion tools
    "notion_search": NotionSearchTool(),
    "notion_read_page": NotionReadPageTool(),
    "notion_create_page": NotionCreatePageTool(),
    "notion_update_page": NotionUpdatePageTool(),
    # X/Twitter tools
    "x_search": XSearchTool(),
    "x_post_tweet": XPostTweetTool(),
    "x_post_thread": XPostThreadTool(),
    "x_get_tweet": XGetTweetTool(),
    # Market data tools
    "market_data_ticker": MarketDataTickerTool(),
    "market_data_ohlcv": MarketDataOHLCVTool(),
    "market_data_trend": MarketDataTrendTool(),
    # Discord
    "discord_tool": DiscordTool(),
}


def load_mission(mission_path: str) -> Dict[str, Any]:
    """Load mission configuration from YAML file."""
    if not os.path.exists(mission_path):
        raise FileNotFoundError(f"Mission file not found: {mission_path}")
    with open(mission_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_tool(tool_name: str) -> BaseTool:
    """Get tool instance by name."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        raise ValueError(
            f"Tool '{tool_name}' not found in registry. Available: {list(TOOL_REGISTRY.keys())}"
        )
    return tool


def create_llm(mission_config: Dict[str, Any]) -> LLM:
    """
    Create LLM instance from mission configuration.
    Supports OpenAI-compatible gateways, Ollama, OpenRouter, Anthropic, Gemini, Groq, etc.
    """
    llm_config = mission_config.get("llm", {})

    raw_model = llm_config.get("model", "gh/gpt-4o-mini-2024-07-18")
    provider = llm_config.get("provider", "openai").lower()
    base_url = llm_config.get("base_url") or os.getenv("OPENAI_API_BASE")
    api_key = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")

    # Format model name with provider prefix if not already present
    if "/" in raw_model and not any(raw_model.startswith(p + "/") for p in ["ollama", "openai", "anthropic", "gemini", "groq", "openrouter"]):
        # Models with org prefix like "gh/gpt-4o-mini" under openai gateway
        model_name = f"{provider}/{raw_model}" if provider else f"openai/{raw_model}"
    elif "/" not in raw_model:
        model_name = f"{provider}/{raw_model}" if provider else f"openai/{raw_model}"
    else:
        model_name = raw_model

    # Set default localhost base_url for openai compatible gateways if not provided
    if not base_url and (provider == "openai" or model_name.startswith("openai/")):
        base_url = "http://localhost:20128/v1"

    # Ollama defaults
    if provider == "ollama" or model_name.startswith("ollama/"):
        if not base_url:
            base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        if not api_key:
            api_key = "ollama"  # dummy key for litellm

    if not api_key and not (provider == "ollama" or model_name.startswith("ollama/")):
        raise ValueError(
            "API key not found. Please set OPENAI_API_KEY env var or provide 'api_key' in mission.yaml"
        )

    llm_kwargs: Dict[str, Any] = {
        "model": model_name,
        "temperature": llm_config.get("temperature", 0.7),
        "max_tokens": llm_config.get("max_tokens", 4096),
    }
    if base_url:
        llm_kwargs["base_url"] = base_url
    if api_key:
        llm_kwargs["api_key"] = api_key

    return LLM(**llm_kwargs)


def build_agents(agents_config: List[Dict[str, Any]], llm: LLM) -> List[Agent]:
    """Build Agent objects from configuration."""
    agents = []
    for agent_cfg in agents_config:
        tools = [get_tool(name) for name in agent_cfg.get("tools", [])]

        agent = Agent(
            role=agent_cfg["role"],
            goal=agent_cfg["goal"],
            backstory=agent_cfg["backstory"],
            tools=tools,
            verbose=agent_cfg.get("verbose", True),
            max_iter=agent_cfg.get("max_iter", 10),
            max_rpm=agent_cfg.get("max_rpm", None),
            llm=llm,
        )
        agents.append(agent)
    return agents


def build_tasks(tasks_config: List[Dict[str, Any]], agents: List[Agent]) -> List[Task]:
    """Build Task objects from configuration with O(1) context lookup mapping."""
    agent_by_role = {agent.role: agent for agent in agents}
    tasks = []
    task_by_role = {}

    for task_cfg in tasks_config:
        agent_role = task_cfg["agent"]
        agent = agent_by_role.get(agent_role)
        if not agent:
            raise ValueError(f"Agent with role '{agent_role}' not found.")

        task = Task(
            description=task_cfg["description"],
            expected_output=task_cfg["expected_output"],
            agent=agent,
            context=[],
        )
        tasks.append(task)
        task_by_role[agent_role] = task

    for i, task_cfg in enumerate(tasks_config):
        if "context" in task_cfg:
            context_roles = task_cfg["context"]
            context_tasks = []
            for role in context_roles:
                dep_task = task_by_role.get(role)
                if not dep_task:
                    raise ValueError(f"No task found for agent role '{role}' in context dependencies.")
                context_tasks.append(dep_task)
            tasks[i].context = context_tasks

    return tasks


def build_crew(mission_config: Dict[str, Any]) -> Crew:
    """Build CrewAI crew from mission configuration."""
    llm = create_llm(mission_config)
    agents = build_agents(mission_config["agents"], llm)
    tasks = build_tasks(mission_config["tasks"], agents)

    process_str = mission_config.get("process", "sequential").lower()
    process = Process.hierarchical if process_str == "hierarchical" else Process.sequential

    return Crew(
        agents=agents,
        tasks=tasks,
        process=process,
        verbose=mission_config.get("verbose", True),
        memory=mission_config.get("memory", False),
        cache=mission_config.get("cache", True),
        max_rpm=mission_config.get("max_rpm", None),
        share_crew=mission_config.get("share_crew", False),
    )


def run_mission(mission_path: str) -> Any:
    """Load mission and run the crew."""
    mission_config = load_mission(mission_path)
    crew = build_crew(mission_config)
    return crew.kickoff()

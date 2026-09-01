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
    
    Resolution hierarchy:
    1. Provider from mission.yaml (default: 'openai' or inferred from model)
    2. API Key from: mission.yaml -> PROVIDER_API_KEY env -> OPENAI_API_KEY env
    3. Base URL from: mission.yaml -> PROVIDER_API_BASE env -> OPENAI_API_BASE env
    """
    llm_config = mission_config.get("llm", {})

    raw_model = llm_config.get("model", "gpt-4o-mini")
    provider = llm_config.get("provider", "").lower()
    
    # Auto-detect provider if not explicitly given
    if not provider:
        if raw_model.startswith("ollama/"):
            provider = "ollama"
        elif raw_model.startswith("openrouter/"):
            provider = "openrouter"
        elif raw_model.startswith("anthropic/"):
            provider = "anthropic"
        elif raw_model.startswith("gemini/"):
            provider = "gemini"
        elif raw_model.startswith("groq/"):
            provider = "groq"
        else:
            provider = "openai"

    # Normalize model name with provider prefix for LiteLLM
    if not raw_model.startswith(f"{provider}/"):
        model_name = f"{provider}/{raw_model}"
    else:
        model_name = raw_model

    # Resolve API Key
    api_key = (
        llm_config.get("api_key")
        or os.getenv(f"{provider.upper()}_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    # Resolve Base URL
    base_url = (
        llm_config.get("base_url")
        or os.getenv(f"{provider.upper()}_API_BASE")
        or os.getenv("OPENAI_API_BASE")
    )

    # Provider specific defaults
    if provider == "ollama":
        if not base_url:
            base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        if not api_key:
            api_key = "ollama"  # dummy key for litellm
    elif provider == "openai":
        # If running on local server with 9router gateway configured in .env
        if not base_url and os.getenv("OPENAI_API_BASE"):
            base_url = os.getenv("OPENAI_API_BASE")

    if not api_key and provider != "ollama":
        raise ValueError(
            f"API key not found for provider '{provider}'. "
            f"Please set {provider.upper()}_API_KEY (or OPENAI_API_KEY) in .env file."
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

    logger.info("Initializing LLM: provider=%s, model=%s, base_url=%s", provider, model_name, base_url or 'default')
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

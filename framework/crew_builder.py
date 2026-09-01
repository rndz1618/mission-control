"""
CrewAI Crew Builder for Mission Control Framework
Loads mission.yaml and constructs a CrewAI crew.
"""
import yaml
import os
from typing import List, Dict, Any
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from crewai.llm import LLM

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
    with open(mission_path, 'r') as f:
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
    """Create LLM instance from mission configuration."""
    llm_config = mission_config.get("llm", {})

    base_url = llm_config.get("base_url", os.getenv("OPENAI_API_BASE", "http://localhost:20128/v1"))
    api_key = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment or mission config.")
    model = llm_config.get("model", "gh/gpt-4o-mini-2024-07-18")

    return LLM(
        model=f"openai/{model}",
        base_url=base_url,
        api_key=api_key,
        temperature=llm_config.get("temperature", 0.7),
        max_tokens=llm_config.get("max_tokens", 4096),
    )


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
    """Build Task objects from configuration."""
    agent_by_role = {agent.role: agent for agent in agents}

    tasks = []
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

    for i, task_cfg in enumerate(tasks_config):
        if "context" in task_cfg:
            context_roles = task_cfg["context"]
            context_tasks = []
            for role in context_roles:
                for task in tasks:
                    if task.agent.role == role:
                        context_tasks.append(task)
                        break
                else:
                    raise ValueError(f"No task found for agent role '{role}'")
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

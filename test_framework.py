"""
Unit and Integration Tests for Mission Control Framework
"""
import os
import sys
import unittest

# Dynamic project root path resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from framework.crew_builder import (
    load_mission,
    get_tool,
    create_llm,
    build_agents,
    build_tasks,
    build_crew,
    TOOL_REGISTRY,
)


class TestMissionControlFramework(unittest.TestCase):
    def setUp(self):
        self.base_dir = CURRENT_DIR
        self.arah_media_path = os.path.join(self.base_dir, "missions", "arah_media", "mission.yaml")
        self.template_path = os.path.join(self.base_dir, "missions", "template", "mission_template.yaml")

    def test_load_mission_yaml(self):
        """Test that mission YAML files load correctly."""
        cfg = load_mission(self.arah_media_path)
        self.assertIn("mission", cfg)
        self.assertIn("agents", cfg)
        self.assertIn("tasks", cfg)
        self.assertEqual(len(cfg["agents"]), 4)
        self.assertEqual(len(cfg["tasks"]), 4)

    def test_template_mission_yaml(self):
        """Test that template YAML is valid."""
        cfg = load_mission(self.template_path)
        self.assertIn("mission", cfg)
        self.assertIn("agents", cfg)
        self.assertIn("tasks", cfg)

    def test_tool_registry_complete(self):
        """Test all expected tools are in registry."""
        expected = [
            "notion_search", "notion_read_page", "notion_create_page", "notion_update_page",
            "x_search", "x_post_tweet", "x_post_thread", "x_get_tweet",
            "market_data_ticker", "market_data_ohlcv", "market_data_trend",
            "discord_tool"
        ]
        for tool_name in expected:
            self.assertIn(tool_name, TOOL_REGISTRY)
            tool = get_tool(tool_name)
            self.assertIsNotNone(tool)
            self.assertTrue(hasattr(tool, "name"))
            self.assertTrue(hasattr(tool, "description"))

    def test_invalid_tool_raises_error(self):
        """Test asking for non-existent tool raises ValueError."""
        with self.assertRaises(ValueError):
            get_tool("non_existent_tool_12345")

    def test_build_agents(self):
        """Test agent construction from config."""
        cfg = load_mission(self.arah_media_path)
        # Set dummy key for offline test
        os.environ["OPENAI_API_KEY"] = "test-key"
        llm = create_llm(cfg)
        agents = build_agents(cfg["agents"], llm)
        self.assertEqual(len(agents), 4)
        roles = [a.role for a in agents]
        self.assertEqual(roles, ["Media Analyst", "Content Writer", "Content Editor", "Release Manager"])

    def test_build_tasks(self):
        """Test task construction and dependency wiring."""
        cfg = load_mission(self.arah_media_path)
        os.environ["OPENAI_API_KEY"] = "test-key"
        llm = create_llm(cfg)
        agents = build_agents(cfg["agents"], llm)
        tasks = build_tasks(cfg["tasks"], agents)
        self.assertEqual(len(tasks), 4)
        
        # Verify context dependencies
        self.assertEqual(len(tasks[0].context), 0)
        self.assertEqual(len(tasks[1].context), 1)
        self.assertEqual(tasks[1].context[0].agent.role, "Media Analyst")
        self.assertEqual(len(tasks[2].context), 1)
        self.assertEqual(tasks[2].context[0].agent.role, "Content Writer")
        self.assertEqual(len(tasks[3].context), 1)
        self.assertEqual(tasks[3].context[0].agent.role, "Content Editor")

    def test_build_crew(self):
        """Test full crew building without execution."""
        cfg = load_mission(self.arah_media_path)
        os.environ["OPENAI_API_KEY"] = "test-key"
        crew = build_crew(cfg)
        self.assertEqual(len(crew.agents), 4)
        self.assertEqual(len(crew.tasks), 4)
        self.assertFalse(crew.memory)
        self.assertTrue(crew.cache)

    def test_xurl_graceful_fallback(self):
        """x_search must not crash when xurl binary is missing."""
        from framework.tools.x_tool import XSearchTool
        result = XSearchTool()._run(query="AI agents")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_human_input_flag_wired(self):
        """human_input: true in YAML must land on the CrewAI Task."""
        cfg = load_mission(self.arah_media_path)
        os.environ["OPENAI_API_KEY"] = "test-key"
        llm = create_llm(cfg)
        agents = build_agents(cfg["agents"], llm)
        tasks = build_tasks(cfg["tasks"], agents)
        editor_task = next(t for t in tasks if t.agent.role == "Content Editor")
        self.assertTrue(editor_task.human_input)


if __name__ == "__main__":
    unittest.main()

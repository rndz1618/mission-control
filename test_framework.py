"""
Unit and Integration Tests for Mission Control Framework
"""
import os
import sys
import unittest
from unittest.mock import patch

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
        with patch("framework.tools.x_tool.is_cli_available", return_value=False):
            result = XSearchTool()._run(query="AI agents")
            self.assertIn("Notice:", result)
            self.assertIn("unavailable", result)

    def test_notion_tools_fallback(self):
        """Notion tools must return structured notice when ntn is missing."""
        from framework.tools.notion_tool import NotionSearchTool, NotionReadPageTool, NotionCreatePageTool, NotionUpdatePageTool
        with patch("framework.tools.notion_tool.is_cli_available", return_value=False):
            res_search = NotionSearchTool()._run(query="ai trend")
            self.assertIn("Notice:", res_search)
            self.assertIn("Please proceed using your internal knowledge", res_search)

            res_read = NotionReadPageTool()._run(page_id="test-page-123")
            self.assertIn("Notice:", res_read)

            res_create = NotionCreatePageTool()._run(parent_id="p1", title="Test Title")
            self.assertIn("Notice:", res_create)

            res_update = NotionUpdatePageTool()._run(page_id="p1", content="New Content")
            self.assertIn("Notice:", res_update)

    def test_market_data_tools_fallback(self):
        """Market data tools must return structured notice when script is missing."""
        from framework.tools.market_data_tool import MarketDataTickerTool, MarketDataOHLCVTool, MarketDataTrendTool
        with patch("framework.tools.market_data_tool.is_script_available", return_value=False):
            res_ticker = MarketDataTickerTool()._run(symbol="BTC/USDT")
            self.assertIn("Notice:", res_ticker)
            self.assertIn("Please proceed with internal estimation", res_ticker)

            res_ohlcv = MarketDataOHLCVTool()._run(symbol="BTC/USDT")
            self.assertIn("Notice:", res_ohlcv)

            res_trend = MarketDataTrendTool()._run(symbol="BTC/USDT")
            self.assertIn("Notice:", res_trend)
            self.assertIn("Please proceed with internal technical analysis", res_trend)

    def test_human_input_flag_wired(self):
        """human_input: true in YAML must land on the CrewAI Task."""
        cfg = load_mission(self.arah_media_path)
        os.environ["OPENAI_API_KEY"] = "test-key"
        llm = create_llm(cfg)
        agents = build_agents(cfg["agents"], llm)
        tasks = build_tasks(cfg["tasks"], agents, skip_human_input=False)
        editor_task = next(t for t in tasks if t.agent.role == "Content Editor")
        self.assertTrue(editor_task.human_input)

    def test_skip_human_input_for_headless(self):
        """Discord/cron runs must disable CrewAI stdin human_input."""
        cfg = load_mission(self.arah_media_path)
        os.environ["OPENAI_API_KEY"] = "test-key"
        llm = create_llm(cfg)
        agents = build_agents(cfg["agents"], llm)
        tasks = build_tasks(cfg["tasks"], agents, skip_human_input=True)
        editor_task = next(t for t in tasks if t.agent.role == "Content Editor")
        self.assertFalse(editor_task.human_input)

    def test_discord_bridge_queue(self):
        """Pending approval queue must persist and update status."""
        import tempfile
        from pathlib import Path
        import discord_bridge

        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = str(Path(tmp) / "pending_approvals.json")
            with patch.object(discord_bridge, "APPROVAL_FILE", tmp_file), \
                 patch.object(discord_bridge, "STATE_DIR", tmp):
                sid = discord_bridge.save_pending_approval(
                    "arah_media",
                    drafts="Draft 1: hello",
                    context_meta={"topic": "AI", "audience": "Devs"},
                )
                self.assertTrue(sid.startswith("arah_media_"))
                self.assertEqual(len(sid.split("_")[-1]), 8)
                pending = discord_bridge.get_latest_pending_approval()
                self.assertIsNotNone(pending)
                self.assertEqual(pending["id"], sid)
                self.assertEqual(pending["status"], "PENDING_APPROVAL")
                ok = discord_bridge.update_approval_status(sid, "APPROVED", notes="ok")
                self.assertTrue(ok)
                leftover = discord_bridge.get_latest_pending_approval()
                self.assertIsNone(leftover)

    def test_discord_bridge_concurrent_writes(self):
        """fcntl lock must keep concurrent writers from dropping records."""
        import tempfile
        import threading
        from pathlib import Path
        import discord_bridge

        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = str(Path(tmp) / "pending_approvals.json")
            with patch.object(discord_bridge, "APPROVAL_FILE", tmp_file), \
                 patch.object(discord_bridge, "STATE_DIR", tmp):
                ids = []

                def worker(i):
                    sid = discord_bridge.save_pending_approval(
                        f"mission{i}", drafts=f"d{i}", context_meta={}
                    )
                    ids.append(sid)

                threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                data = discord_bridge._locked_read()
                self.assertEqual(len(data), 8)
                self.assertEqual(len(set(ids)), 8)

    def test_smart_truncate_preserves_newline(self):
        """Discord formatter must not slice mid-line when possible."""
        import discord_bridge
        blob = "\n".join([f"line {i} " + ("x" * 80) for i in range(40)])
        out = discord_bridge._smart_truncate(blob, 1400)
        self.assertIn("truncated", out)
        self.assertLessEqual(len(out), 1500)
        self.assertFalse(out.startswith("..."))

    def test_run_bridge_records_failure(self):
        """Failed missions must land in the queue as FAILED, not raise raw."""
        import tempfile
        from pathlib import Path
        import discord_bridge
        import run_bridge

        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = str(Path(tmp) / "pending_approvals.json")
            with patch.object(discord_bridge, "APPROVAL_FILE", tmp_file), \
                 patch.object(discord_bridge, "STATE_DIR", tmp), \
                 patch.object(run_bridge, "run_mission", side_effect=RuntimeError("boom")):
                res = run_bridge.execute_and_queue("arah_media", {"topic": "x"})
                self.assertEqual(res["status"], "FAILED")
                item = discord_bridge.get_approval(res["session_id"])
                self.assertEqual(item["status"], "FAILED")
                self.assertIn("boom", res["discord_message"])


if __name__ == "__main__":
    unittest.main()

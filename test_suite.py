import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from shared_state.state_manager import state_manager
from tools.safety_sentinel import safety_sentinel, ActionRisk
from tools.file_ops import file_tools
from tools.shell_control import shell_tools
from tools.app_control import app_tools
from agents.manager import manager_agent
from agents.thinker import thinker_agent
from agents.coder import coder_agent
from agents.qa_debugger import qa_agent

class TestUltronAssistant(unittest.TestCase):
    """Automated verification suite for Ultron."""

    def test_01_database_and_state(self):
        """Test shared state recording and retrieval."""
        event_id = state_manager.record_action(
            agent_name="TestAgent",
            action="UNIT_TEST_ACTION",
            target="test_target",
            details={"key": "val"}
        )
        self.assertIsInstance(event_id, int)
        history = state_manager.get_history(limit=5)
        self.assertTrue(any(ev["action"] == "UNIT_TEST_ACTION" for ev in history))

    def test_02_safety_sentinel_risk_classification(self):
        """Test risk detection on dangerous versus safe actions."""
        self.assertEqual(safety_sentinel.evaluate_risk("open_app"), ActionRisk.LOW)
        self.assertEqual(safety_sentinel.evaluate_risk("read_file"), ActionRisk.LOW)
        self.assertEqual(safety_sentinel.evaluate_risk("delete_path"), ActionRisk.HIGH)
        self.assertEqual(safety_sentinel.evaluate_risk("create_ad_campaign"), ActionRisk.HIGH)
        self.assertEqual(safety_sentinel.evaluate_risk("post_to_instagram"), ActionRisk.HIGH)

    def test_03_file_operations(self):
        """Test safe file operations."""
        test_dir = PROJECT_ROOT / "data" / "test_sandbox"
        res_dir = file_tools.create_directory(str(test_dir))
        self.assertTrue(res_dir.get("success"))

        test_file = test_dir / "sample.txt"
        res_write = file_tools.write_file(str(test_file), "Ultron Unit Test Content")
        self.assertTrue(res_write.get("success"))

        res_read = file_tools.read_file(str(test_file))
        self.assertEqual(res_read.get("content"), "Ultron Unit Test Content")

    def test_04_shell_execution(self):
        """Test PowerShell execution."""
        res = shell_tools.execute_command("Write-Output 'UltronOnline'")
        self.assertTrue(res.get("success"))
        self.assertIn("UltronOnline", res.get("stdout"))

    def test_05_multi_agent_coder_and_qa(self):
        """Test Coder and QA agent cooperation."""
        coder_res = coder_agent.develop_project("TestProject", "Simple Python hello world script")
        self.assertTrue(coder_res.get("success"))
        self.assertTrue(len(coder_res.get("files", [])) > 0)

        # Check syntax with QA agent
        for f in coder_res.get("files", []):
            if f.endswith(".py"):
                qa_res = qa_agent.verify_python_syntax(f)
                self.assertTrue(qa_res.get("passed"))

    def test_06_manager_orchestration(self):
        """Test Manager agent handling a full user command."""
        res = manager_agent.handle_user_command("Open browser and go to google.com")
        self.assertTrue(res.get("success"))
        self.assertIsNotNone(res.get("spoken_response"))

if __name__ == "__main__":
    unittest.main()

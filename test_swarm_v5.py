import unittest
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

class TestUltronSwarmV5(unittest.TestCase):
    """
    Test Suite for Ultron 5.0 Multi-LLM Swarm Harness & Specialized Brains.
    """

    def test_01_swarm_harness_registration(self):
        """Test Swarm Harness blackboard state and brain registration."""
        from agents.brains import swarm_harness, brain_browser, brain_os_device, brain_big_tasks, brain_telephony
        
        self.assertIsNotNone(swarm_harness.get_brain("browser"))
        self.assertIsNotNone(swarm_harness.get_brain("os_device"))
        self.assertIsNotNone(swarm_harness.get_brain("big_tasks"))
        self.assertIsNotNone(swarm_harness.get_brain("telephony"))
        
        # Test Blackboard state update and event bus
        events_received = []
        swarm_harness.blackboard.subscribe(lambda ev: events_received.append(ev))
        swarm_harness.blackboard.set("active_goal", "Dominate Web SEO & Telephony", source_brain="Test")
        
        self.assertEqual(swarm_harness.blackboard.get("active_goal"), "Dominate Web SEO & Telephony")
        self.assertGreaterEqual(len(events_received), 1)
        print("[PASS] Test 1: Swarm Harness & Blackboard Event Bus verified.")

    def test_02_browser_brain_navigation(self):
        """Test Browser Brain reasoning over Google Drive and Hostinger."""
        from agents.brains.brain_browser import brain_browser
        
        res = brain_browser.plan_and_execute("open google drive in a tab")
        self.assertEqual(res["brain"], "browser")
        self.assertIn("plan", res)
        self.assertTrue(res["result"]["success"])
        print(f"[PASS] Test 2: Browser Brain executed '{res['plan']['summary']}'. Spoken: {res['spoken_response']}")

    def test_03_os_device_brain_control(self):
        """Test OS & Device Brain inspecting telemetry and managing hardware."""
        from agents.brains.brain_os_device import brain_os_device
        
        res = brain_os_device.plan_and_execute("inspect system telemetry and hardware vitals")
        self.assertEqual(res["brain"], "os_device")
        self.assertTrue(res["result"]["success"])
        print(f"[PASS] Test 3: OS/Device Brain executed '{res['plan']['summary']}'.")

    def test_04_big_task_meta_prompting(self):
        """Test Big Task Brain generating meta-prompts for v0/Claude and Headless CMS SEO."""
        from agents.brains.brain_big_tasks import brain_big_tasks
        
        prompt = "Create a master prompt for v0 to build a futuristic digital marketing agency landing page for Risala Digital in Jodhpur"
        res = brain_big_tasks.plan_and_execute(prompt)
        
        self.assertEqual(res["brain"], "big_tasks")
        self.assertIn("payload", res)
        self.assertIn("meta_prompt_text", res["payload"])
        print(f"[PASS] Test 4: Big Task Brain formulated Meta-Prompt for {res['payload'].get('target_ai_model', 'v0')}: '{res['title']}'")

    def test_05_telephony_live_calling_pipeline(self):
        """Test Telephony Brain generating call scripts and structured field schemas."""
        from agents.brains.brain_telephony import brain_telephony
        
        prompt = "Call Grand Palace Hotel at +919876543210 and book a table for 3 at 8:00 PM tonight under Dushyant"
        res = brain_telephony.plan_and_execute(prompt)
        
        self.assertEqual(res["brain"], "telephony")
        self.assertIn("call_script", res["plan"])
        self.assertIn("expected_fields", res["plan"])
        print(f"[PASS] Test 5: Telephony Brain formulated Call Script: '{res['plan']['call_script'][:80]}...'")

    def test_06_quality_critic_reflection(self):
        """Test Quality Critic independently auditing SEO metadata for Indian/Jodhpur market."""
        from agents.quality_critic import quality_critic
        
        eval_result = quality_critic.evaluate_seo_content(
            page_title="About Us",
            focus_keyword="Digital Marketing Agency in Jodhpur",
            meta_title="Digital Marketing Agency in Jodhpur | Risala Digital",
            meta_description="Partner with the top digital marketing agency in Jodhpur delivering high-ROI performance marketing and Headless CMS builds. Contact us today!",
            page_copy="Risala Digital Marketing is the premier performance agency based in Jodhpur, Rajasthan..."
        )
        
        self.assertGreaterEqual(eval_result["score"], 8)
        self.assertTrue(eval_result["approved"])
        print(f"[PASS] Test 6: Quality Critic Score: {eval_result['score']}/10. Approved: {eval_result['approved']}")

    def test_07_manager_swarm_commander_end_to_end(self):
        """Test Manager Swarm Commander processing high-level natural instructions."""
        from agents.manager import manager_agent
        
        # Test Big Task Routing
        res = manager_agent.handle_user_command("plan an app wireframe and generate an SEO strategy for Risala Digital Marketing")
        self.assertTrue(res["success"])
        self.assertIn("spoken_response", res)
        print(f"[PASS] Test 7: Swarm Commander Orchestration Response:\n   \"{res['spoken_response']}\"")

if __name__ == "__main__":
    unittest.main()

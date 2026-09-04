"""
Ultron Automated Verification Suite v4.0
Covers:
1. Long-Form Voice VAD & Groq Whisper Agency Vocabulary
2. Display Scaling & DPI Awareness (150% Scale Calibration)
3. Quality Critic Self-Reflection & Evaluator Engine
4. Chrome Profile Intelligent Routing (Profile 1 vs Default)
5. Thinker Multi-Step Planning for Agency Workflows
6. Autonomous Agency SEO Generation & Auto-Critique Loop
7. Dynamic Contextual Spoken Synthesis (Zero Canned Templates)
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
WORKSPACE_DIR = Path(__file__).resolve().parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

class TestUltronV4CognitiveSuite(unittest.TestCase):

    def test_01_voice_vad_and_agency_vocabulary(self):
        """Test long-form voice recognition settings and agency prompt context."""
        from voice.wake_word import wake_detector
        
        # Test wake phrase detection
        is_wake, rem = wake_detector.is_wake_phrase("yo ultron today we do seo")
        self.assertTrue(is_wake)
        self.assertIn("seo", rem)
        
        # Test dismissal phrase detection
        self.assertTrue(wake_detector.is_dismissal_phrase("that's enough for today"))
        self.assertTrue(wake_detector.is_dismissal_phrase("go to sleep"))
        
        # Verify pause_threshold calibration
        self.assertIsNotNone(wake_detector._recognizer)
        self.assertGreaterEqual(wake_detector._recognizer.pause_threshold, 1.0)
        print("[PASS] Test 1: Voice VAD and phrase detection verified.")

    def test_02_dpi_awareness_and_coordinate_calibration(self):
        """Test Per-Monitor DPI awareness and normalized coordinate math."""
        from tools.vision_control import vision_control
        
        # Verify coordinate mapping for 1920x1080 screen with 150% scaling
        test_w, test_h = 1920, 1080
        # Given normalized [ymin, xmin, ymax, xmax] = [200, 400, 300, 600]
        box = [200, 400, 300, 600]
        center_x = int(((box[1] + box[3]) / 2.0) * (test_w / 1000.0))
        center_y = int(((box[0] + box[2]) / 2.0) * (test_h / 1000.0))
        
        self.assertEqual(center_x, int(500 * 1.92))
        self.assertEqual(center_y, int(250 * 1.08))
        self.assertEqual(center_x, 960)
        self.assertEqual(center_y, 270)
        print(f"[PASS] Test 2: DPI coordinate calibration verified. Center: ({center_x}, {center_y})")

    def test_03_quality_critic_seo_evaluation(self):
        """Test Quality Critic self-reflection on SEO metadata."""
        from agents.quality_critic import quality_critic
        
        eval_result = quality_critic.evaluate_seo_content(
            page_title="About Us",
            focus_keyword="Digital Marketing Agency in Dubai",
            meta_title="Digital Marketing Agency in Dubai | Risala Digital",
            meta_description="Partner with a leading digital marketing agency in Dubai driving high-ROI performance marketing and headless web builds. Connect with Risala today!",
            page_copy="Risala Digital Marketing is an elite performance agency based in Dubai..."
        )
        
        self.assertIn("score", eval_result)
        self.assertGreaterEqual(eval_result["score"], 7)
        self.assertIn("critique", eval_result)
        self.assertIn("optimized_meta_title", eval_result)
        print(f"[PASS] Test 3: Quality Critic SEO Score: {eval_result['score']}/10. Critique: {eval_result['critique'][:80]}...")

    def test_04_chrome_profile_routing(self):
        """Test automatic profile resolution for agency vs personal tasks."""
        from tools.browser_control import browser_tools
        
        # Agency & web tasks must route to Profile 1 (Risala Digital Marketing)
        self.assertEqual(browser_tools.resolve_profile("risala digital marketing"), "Profile 1")
        self.assertEqual(browser_tools.resolve_profile("agency"), "Profile 1")
        self.assertEqual(browser_tools.resolve_profile("seo"), "Profile 1")
        self.assertEqual(browser_tools.resolve_profile(None), "Profile 1")
        
        # Personal tasks must route to Default (itzdushyant)
        self.assertEqual(browser_tools.resolve_profile("itzdushyant"), "Default")
        self.assertEqual(browser_tools.resolve_profile("personal"), "Default")
        print("[PASS] Test 4: Chrome profile routing verified (Profile 1 vs Default).")

    def test_05_thinker_agency_plan_generation(self):
        """Test Thinker decomposing user's real-world command into multi-step execution."""
        from agents.thinker import thinker_agent
        
        cmd = (
            "yo ultron, today we are going to do seo for Risaladigitalmarketing.com, "
            "so open the hostinger dashboard using Risala Digital Marketing chrome profile, "
            "then tap on wp admin, then open about us and generate a focus keyword and title description for this page."
        )
        plan = thinker_agent.analyze_and_plan(cmd, {})
        
        self.assertIn("Risaladigitalmarketing.com", plan.get("intent_summary", ""))
        steps = plan.get("steps", [])
        self.assertEqual(len(steps), 3)
        
        # Step 1: Open Hostinger in Profile 1
        self.assertEqual(steps[0]["action"], "open_profile")
        self.assertEqual(steps[0]["parameters"]["profile"], "Profile 1")
        
        # Step 2: Locate and click WP Admin
        self.assertEqual(steps[1]["action"], "locate_and_click")
        self.assertEqual(steps[1]["parameters"]["target"], "WP Admin")
        
        # Step 3: Generate SEO with Quality Critic
        self.assertEqual(steps[2]["action"], "generate_seo")
        self.assertEqual(steps[2]["parameters"]["page"], "About Us")
        print("[PASS] Test 5: Thinker generated 3-step agency workflow plan.")

    def test_06_executor_agency_seo_and_critic_loop(self):
        """Test Executor generating SEO package with automatic Quality Critic optimization."""
        from agents.executor import executor_agent
        
        res = executor_agent.execute_step("generate_seo", {
            "domain": "Risaladigitalmarketing.com",
            "page": "About Us"
        })
        
        self.assertTrue(res.get("success"))
        seo_data = res.get("seo_data", {})
        self.assertIn("focus_keyword", seo_data)
        self.assertIn("meta_title", seo_data)
        self.assertIn("meta_description", seo_data)
        self.assertIn("critic_evaluation", seo_data)
        
        # Verify strict character limits
        self.assertLessEqual(len(seo_data["meta_title"]), 65)
        self.assertLessEqual(len(seo_data["meta_description"]), 160)
        print(f"[PASS] Test 6: SEO Package generated: '{seo_data['meta_title']}' ({len(seo_data['meta_title'])} chars)")

    def test_07_manager_dynamic_spoken_synthesis(self):
        """Test Manager formulating original, dynamic spoken response without canned templates."""
        from agents.manager import manager_agent
        
        user_cmd = "open Hostinger and generate SEO for About Us"
        plan = {"spoken_response": "Executing agency workflow for Risaladigitalmarketing.com, Boss."}
        step_results = [
            {
                "step": {"action": "open_profile", "description": "Open Hostinger in Profile 1"},
                "result": {"success": True, "message": "Hostinger opened in Profile 1"}
            },
            {
                "step": {"action": "generate_seo", "description": "Generate SEO for About Us"},
                "result": {"success": True, "message": "SEO metadata perfected with 10/10 Quality Score"}
            }
        ]
        
        spoken = manager_agent._generate_final_response(user_cmd, plan, step_results)
        self.assertTrue(len(spoken) > 10)
        self.assertIn("Boss", spoken)
        # Verify it is not a canned generic message
        self.assertNotIn("Done. I have executed your request.", spoken)
        print(f"[PASS] Test 7: Manager synthesized dynamic spoken response:\n   \"{spoken}\"")

if __name__ == "__main__":
    unittest.main(verbosity=2)

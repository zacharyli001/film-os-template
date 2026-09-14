from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/check_model_compatibility.py"


class ModelCompatibilityTests(unittest.TestCase):
    def run_check(self, capability_lines: str, task: str) -> subprocess.CompletedProcess[str]:
        report = """schema_version: film-os/model-capability-report/v1
provider: test
model_id: test-model
client: test-client
capability_report_status: verified
capabilities:
""" + capability_lines
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8") as handle:
            handle.write(report)
            handle.flush()
            return subprocess.run(
                ["python3", str(TOOL), "--report", handle.name, "--task", task],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_text_runtime_can_do_creative_text(self) -> None:
        result = self.run_check(
            "  text_generation: supported\n  instruction_following: supported\n  file_read: supported\n",
            "creative_text",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("status=compatible", result.stdout)

    def test_text_runtime_cannot_claim_visual_qc(self) -> None:
        result = self.run_check(
            "  instruction_following: supported\n  vision_input: unsupported\n",
            "visual_qc",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("fallback=visual_qc_not_performed", result.stdout)

    def test_unknown_capability_is_restricted(self) -> None:
        result = self.run_check(
            "  instruction_following: supported\n  file_read: supported\n  file_write: unknown\n  tool_execution: supported\n",
            "package_export",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("file_write", result.stdout)

    def test_blender_previz_requires_observed_control_and_capture(self) -> None:
        result = self.run_check(
            "  instruction_following: supported\n"
            "  file_read: supported\n"
            "  file_write: supported\n"
            "  tool_execution: supported\n"
            "  blender_scene_control: unknown\n"
            "  viewport_capture: unsupported\n",
            "blender_previz",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("blender_scene_control", result.stdout)
        self.assertIn("viewport_capture", result.stdout)
        self.assertIn("fallback=previz_plan_only_no_blender_execution", result.stdout)


if __name__ == "__main__":
    unittest.main()

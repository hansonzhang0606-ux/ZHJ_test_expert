import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "workbuddy" / "zhj-testing-expert"

class WorkBuddyPackageTests(unittest.TestCase):
    def test_manifest_exposes_required_expert_metadata(self):
        manifest = json.loads((PACKAGE / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("\u667a\u6167\u8bb0\u6d4b\u8bd5\u4e13\u5bb6", manifest["displayName"]["zh"])
        self.assertEqual("1.1.0", manifest["version"])
        self.assertEqual(3, len(manifest["tags"]))
        self.assertEqual(3, len(manifest["quickPrompts"]))
        self.assertEqual("./avatars/zhj-testing-expert.svg", manifest["avatar"])

    def test_agent_maps_all_eight_stages_and_allows_independent_case_records(self):
        agent = (PACKAGE / "agents" / "zhj-testing-expert.md").read_text(encoding="utf-8")
        for stage in ("0 export", "1 document", "2 review", "3 test-case", "4 smoke-case", "5 AI", "7 knowledge", "8 SVN"):
            self.assertIn(stage, agent)
        self.assertIn("standalone", agent)
        self.assertIn("same `session_id`", agent)

    def test_batch_sync_rejects_missing_business_line(self):
        batch = (ROOT / "ZHJ_test_skills" / "time-tracking-skill" / "scripts" / "sync_task.bat").read_text(encoding="utf-8")
        self.assertNotIn('set "BIZ_LINE=\u667a\u6167\u8bb0+\u8fd0\u8425\u7cfb\u7edf"', batch)
        self.assertIn("ERROR: business line is required", batch)

if __name__ == "__main__":
    unittest.main()

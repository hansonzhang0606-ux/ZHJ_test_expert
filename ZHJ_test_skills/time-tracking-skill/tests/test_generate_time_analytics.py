import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPT_DIR / "generate_time_analytics.py"


def load_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("generate_time_analytics_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerateTimeAnalyticsTests(unittest.TestCase):
    def test_statistics_group_custom_steps_by_canonical_step_name(self):
        module = load_module()
        records = [
            {
                "employee": "李静",
                "user_story": "PRJ-1 统计规范化",
                "step": "旧步骤名称",
                "step_code": "05",
                "time_saved_hours": 2,
                "time_saved_pd": 0.25,
                "total_hours": 2,
            },
            {
                "employee": "李静",
                "user_story": "PRJ-1 统计规范化",
                "step": "另一旧名称",
                "step_code": "08",
                "time_saved_hours": 1,
                "time_saved_pd": 0.125,
                "total_hours": 1,
            },
        ]

        stats = module.compute_stats(records)

        self.assertIn("AI 对比入库", stats["by_step"])
        self.assertIn("SVN 归档上传", stats["by_step"])
        self.assertEqual(2, stats["by_step"]["AI 对比入库"]["hours"])
        self.assertEqual(1, stats["by_step"]["SVN 归档上传"]["hours"])
        self.assertNotIn("旧步骤名称", stats["by_step"])


if __name__ == "__main__":
    unittest.main()

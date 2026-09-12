import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPT_DIR / "sync_to_mysql.py"


def load_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("sync_to_mysql_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureCursor:
    def __init__(self):
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _sql, params):
        self.params = params


class CaptureConnection:
    def __init__(self):
        self.cursor_instance = CaptureCursor()

    def cursor(self):
        return self.cursor_instance


class SyncToMySQLTests(unittest.TestCase):
    def test_upsert_normalizes_custom_step_names_from_step_codes(self):
        module = load_module()

        for step_code, expected_step in (("05", "AI 对比入库"), ("08", "SVN 归档上传")):
            with self.subTest(step_code=step_code):
                conn = CaptureConnection()
                module.upsert_record(
                    conn,
                    "agent_time_tracking",
                    {
                        "timestamp": "2026-09-01T10:00:00+08:00",
                        "date": "2026-09-01",
                        "biz_line": "智慧记+运营系统",
                        "employee": "李静",
                        "user_story": "PRJ-1 步骤规范化",
                        "step": "旧步骤名称",
                        "step_code": step_code,
                        "time_saved_hours": 1,
                        "time_saved_pd": 0.125,
                        "total_hours": 1,
                        "agent_start_time": "",
                        "agent_end_time": "",
                        "agent_duration_minutes": None,
                        "remark": "",
                    },
                    "智慧记+运营系统",
                    "ZHJ",
                )

                self.assertEqual(expected_step, conn.cursor_instance.params["step"])
                self.assertEqual(step_code, conn.cursor_instance.params["step_code"])


if __name__ == "__main__":
    unittest.main()

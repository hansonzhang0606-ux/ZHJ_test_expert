import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPT_DIR / "update_step_metadata.py"


def load_module():
    spec = importlib.util.spec_from_file_location("update_step_metadata_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureCursor:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


class CaptureConnection:
    def __init__(self):
        self.cursor_instance = CaptureCursor()

    def cursor(self):
        return self.cursor_instance


class UpdateStepMetadataTests(unittest.TestCase):
    def test_updates_step_comment_with_all_supported_codes(self):
        self.assertTrue(SCRIPT.exists(), "缺少一次性 step 元数据更新脚本")
        sys.path.insert(0, str(SCRIPT_DIR))
        module = load_module()
        conn = CaptureConnection()

        module.update_step_comment(conn, "agent_time_tracking")

        sql, params = conn.cursor_instance.calls[-1]
        self.assertIn("ALTER TABLE `agent_time_tracking`", sql)
        comment = params[0]
        for expected in (
            "导出需求（00）",
            "文档整理（01）",
            "需求评审（02）",
            "生成测试点（04）",
            "AI 对比入库（05）",
            "生成用例（06）",
            "入库知识库（07）",
            "SVN 归档上传（08）",
        ):
            self.assertIn(expected, comment)


if __name__ == "__main__":
    unittest.main()

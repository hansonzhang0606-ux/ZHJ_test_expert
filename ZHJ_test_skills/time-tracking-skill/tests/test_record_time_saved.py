import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "record_time_saved.py"


def load_module():
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("record_time_saved", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordTimeSavedTests(unittest.TestCase):
    def test_rejects_employee_missing_from_roster_without_writing(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记+运营系统"],
                    "biz_line_code": ["ZHJ"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            with redirect_stdout(io.StringIO()):
                with self.assertRaises(PermissionError) as raised:
                    module.record(
                        "未授权员工",
                        "PRJ-1 示例",
                        "文档整理",
                        "01",
                        hours=1,
                        biz_line="智慧记+运营系统",
                    )

            self.assertIn("联系管理员", str(raised.exception))
            self.assertFalse(records_path.exists())

    def test_rejects_business_line_not_assigned_to_employee_without_writing(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记零售"],
                    "biz_line_code": ["ZHJLS"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            with redirect_stdout(io.StringIO()):
                with self.assertRaises(PermissionError) as raised:
                    module.record(
                        "李静",
                        "PRJ-1 示例",
                        "文档整理",
                        "01",
                        hours=1,
                        biz_line="国际版Ailit",
                    )

            self.assertIn("联系管理员", str(raised.exception))
            self.assertFalse(records_path.exists())

    def test_merge_existing_accumulates_stage_three_and_four(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记+运营系统"],
                    "biz_line_code": ["ZHJ"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            with redirect_stdout(io.StringIO()):
                module.record(
                    "李静", "PRJ-1 示例", "生成用例", "06", hours=2,
                    biz_line="智慧记+运营系统", session_id="session-001",
                )
                merged = module.record(
                    "李静", "PRJ-1 示例", "生成用例", "06", hours=1.5,
                    biz_line="智慧记+运营系统", session_id="session-001",
                    merge_existing=True,
                )

            records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(records))
            self.assertEqual(3.5, merged["time_saved_hours"])
            self.assertEqual(0.44, merged["time_saved_pd"])
            self.assertEqual(3.5, records[0]["total_hours"])
            self.assertEqual("session-001", records[0]["session_id"])

    def test_stage_four_without_stage_three_is_saved_standalone(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记+运营系统"],
                    "biz_line_code": ["ZHJ"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            try:
                with redirect_stdout(io.StringIO()):
                    saved = module.record(
                        "李静", "PRJ-2 仅冒烟", "生成用例", "06", hours=1,
                        biz_line="智慧记+运营系统", session_id="session-only-four",
                        merge_existing=True,
                    )
            except LookupError as exc:
                self.fail(f"仅执行④时不应拒绝保存：{exc}")

            records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(records))
            self.assertEqual(1.0, saved["total_hours"])
            self.assertEqual("生成用例", records[0]["step"])
            self.assertEqual("06", records[0]["step_code"])

    def test_stage_four_from_a_different_session_is_not_cross_merged(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记+运营系统"],
                    "biz_line_code": ["ZHJ"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            with redirect_stdout(io.StringIO()):
                module.record(
                    "李静", "PRJ-1 示例", "生成用例", "06", hours=2,
                    biz_line="智慧记+运营系统", session_id="session-003",
                )
                try:
                    module.record(
                        "李静", "PRJ-1 示例", "生成用例", "06", hours=1.5,
                        biz_line="智慧记+运营系统", session_id="session-004",
                        merge_existing=True,
                    )
                except LookupError as exc:
                    self.fail(f"不同会话的④应作为仅④独立保存：{exc}")

            records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(2, len(records))
            self.assertEqual(2.0, records[0]["total_hours"])
            self.assertEqual(1.5, records[1]["total_hours"])
            self.assertEqual("session-004", records[1]["session_id"])

    def test_stage_three_requires_session_id_and_prints_continue_reminder(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记+运营系统"],
                    "biz_line_code": ["ZHJ"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            with redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    module.record(
                        "李静", "PRJ-1 示例", "生成用例", "06", hours=2,
                        biz_line="智慧记+运营系统",
                    )

            output = io.StringIO()
            with redirect_stdout(output):
                module.record(
                    "李静", "PRJ-1 示例", "生成用例", "06", hours=2,
                    biz_line="智慧记+运营系统", session_id="session-005",
                )

            self.assertIn("当前会话继续完成④", output.getvalue())
            self.assertIn("session-005", output.getvalue())
            records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(records))
            self.assertEqual(2.0, records[0]["total_hours"])

    def test_known_step_codes_override_noncanonical_step_names(self):
        module = load_module()
        module.load_team_roster = lambda: {
            "members": [
                {
                    "name": "李静",
                    "role": "功能测试",
                    "active": True,
                    "biz_line": ["智慧记+运营系统"],
                    "biz_line_code": ["ZHJ"],
                }
            ],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            for index, (step_code, expected_step) in enumerate(
                (("05", "AI 对比入库"), ("08", "SVN 归档上传")), start=1
            ):
                with self.subTest(step_code=step_code):
                    with redirect_stdout(io.StringIO()):
                        saved = module.record(
                            "李静", f"PRJ-{index} 步骤规范化", "旧步骤名称", step_code,
                            hours=1, biz_line="智慧记+运营系统",
                        )
                    self.assertEqual(expected_step, saved["step"])


if __name__ == "__main__":
    unittest.main()

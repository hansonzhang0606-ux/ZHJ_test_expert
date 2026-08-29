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
    def test_merge_existing_accumulates_stage_three_and_four(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            records_path = Path(temp_dir) / "records.jsonl"
            module.get_records_path = lambda _biz_line: str(records_path)

            with redirect_stdout(io.StringIO()):
                module.record(
                    "李静", "PRJ-1 示例", "生成用例", "06", hours=2,
                    biz_line="智慧记+运营系统", skip_validation=True,
                )
                merged = module.record(
                    "李静", "PRJ-1 示例", "生成用例", "06", hours=1.5,
                    biz_line="智慧记+运营系统", skip_validation=True,
                    merge_existing=True,
                )

            records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(records))
            self.assertEqual(3.5, merged["time_saved_hours"])
            self.assertEqual(0.44, merged["time_saved_pd"])
            self.assertEqual(3.5, records[0]["total_hours"])


if __name__ == "__main__":
    unittest.main()

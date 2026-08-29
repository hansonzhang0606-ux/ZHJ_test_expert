import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
HELPER = SCRIPT_DIR / "biz_line_helper.py"
ROSTER_LOADER = SCRIPT_DIR / "load_roster.py"


def load_helper():
    sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("biz_line_helper_under_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_roster_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("load_roster_under_test", ROSTER_LOADER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCursor:
    last_sql = ""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, _params):
        type(self).last_sql = sql
        return None

    def fetchall(self):
        return [
            {"biz_line": "智慧记+运营系统", "name": "跨线员工", "role": "功能测试", "active": 1},
            {"biz_line": "国际版Ailit", "name": "跨线员工", "role": "功能测试", "active": 1},
        ]


class FakeConnection:
    def cursor(self):
        return FakeCursor()

    def close(self):
        return None


class BizLineHelperTests(unittest.TestCase):
    def test_ailit_round_trip_supports_roster_selection_and_mysql_sync(self):
        helper = load_helper()

        self.assertEqual("国际版Ailit", helper.code_to_biz_line("AILIT"))
        self.assertEqual("AILIT", helper.biz_line_to_code("国际版Ailit"))

    def test_roster_derives_codes_from_multiple_chinese_biz_line_rows(self):
        roster_loader = load_roster_module()
        roster_loader.find_mysql_config = lambda: ({"database": "test"}, "test/mysql_config.json")
        roster_loader.pymysql.connect = lambda **_kwargs: FakeConnection()

        roster, _config_path = roster_loader.load_roster_from_mysql()

        self.assertIn(
            "SELECT biz_line, name, role, active FROM agent_team_roster",
            FakeCursor.last_sql,
        )
        self.assertNotIn("biz_line_code", FakeCursor.last_sql)
        self.assertEqual(
            ["ZHJ", "AILIT"],
            roster["跨线员工"]["biz_line_code"],
        )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性更新 agent_time_tracking.step 的字段注释，不修改业务数据。"""

import argparse
import re
import sys

from load_roster import find_mysql_config
from step_helper import STEP_COLUMN_COMMENT
from sync_to_mysql import get_connection


IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


def update_step_comment(conn, table: str) -> None:
    """将 step 字段注释更新为当前统一步骤清单。"""
    if not IDENTIFIER_RE.fullmatch(table or ""):
        raise ValueError(f"非法表名：{table}")
    sql = (
        f"ALTER TABLE `{table}` MODIFY COLUMN `step` "
        "varchar(50) NOT NULL COMMENT %s"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (STEP_COLUMN_COMMENT,))


def main() -> None:
    parser = argparse.ArgumentParser(description="更新 agent_time_tracking.step 字段注释")
    parser.add_argument("--table", default="agent_time_tracking", help="目标表名")
    parser.add_argument("--apply", action="store_true", help="实际执行；未提供时仅展示目标注释")
    args = parser.parse_args()

    if not args.apply:
        print(STEP_COLUMN_COMMENT)
        print("未执行数据库修改；确认后增加 --apply。")
        return

    cfg, _cfg_path = find_mysql_config()
    if not cfg:
        print("错误：未找到 mysql_config.json，请先完成本机 MySQL 配置。", file=sys.stderr)
        raise SystemExit(2)

    conn = get_connection(cfg)
    try:
        update_step_comment(conn, args.table)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"已更新 {args.table}.step 字段注释：{STEP_COLUMN_COMMENT}")


if __name__ == "__main__":
    main()

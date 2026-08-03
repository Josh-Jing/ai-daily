#!/usr/bin/env python3
"""论文去重数据库工具。

用于 AI 日报 cron job 的论文去重。每篇被推送过的论文 URL 作为主键存入
SQLite 数据库，定时任务在选题时查询是否已推送过，git push 成功后再录入。

用法:
    python3 paper_db.py check <url>     # 查询论文是否已存在
    python3 paper_db.py add <url> "标题" # 录入论文
    python3 paper_db.py list            # 列出所有已推送论文

check 输出 EXISTS 或 NEW，退出码 0=已存在，1=未存在。
add    输出 OK 或 ALREADY EXISTS。
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".papers.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS papers (
            url    TEXT PRIMARY KEY,
            title  TEXT NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now', '+8 hours'))
        )
        """
    )
    conn.commit()
    return conn


def cmd_check(url: str) -> int:
    conn = get_conn()
    row = conn.execute("SELECT title FROM papers WHERE url = ?", (url,)).fetchone()
    conn.close()
    if row:
        print(f"EXISTS\t{row[0]}")
        return 0
    print("NEW")
    return 1


def cmd_add(url: str, title: str) -> int:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO papers (url, title) VALUES (?, ?)", (url, title))
        conn.commit()
        print("OK")
        return 0
    except sqlite3.IntegrityError:
        print("ALREADY EXISTS")
        return 0
    finally:
        conn.close()


def cmd_list() -> int:
    conn = get_conn()
    rows = conn.execute(
        "SELECT url, title, added_at FROM papers ORDER BY added_at DESC"
    ).fetchall()
    conn.close()
    if not rows:
        print("(empty)")
        return 0
    for url, title, added_at in rows:
        print(f"{added_at}\t{url}\t{title}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    cmd = sys.argv[1]

    if cmd == "check":
        if len(sys.argv) < 3:
            print("Usage: paper_db.py check <url>", file=sys.stderr)
            return 2
        return cmd_check(sys.argv[2])

    if cmd == "add":
        if len(sys.argv) < 4:
            print('Usage: paper_db.py add <url> "标题"', file=sys.stderr)
            return 2
        return cmd_add(sys.argv[2], sys.argv[3])

    if cmd == "list":
        return cmd_list()

    print(f"Unknown command: {cmd}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

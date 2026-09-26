"""
TESTS/DB_STATUS_CHECKS.PY — sandbox checks for the DB status window's data
layer (`database_handler.db_status`): the read-only one-pass summary behind
double-clicking the sync medallion. Pure sqlite on temp files — no Qt.
"""

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


from core_engine.database_handler import db_status

with tempfile.TemporaryDirectory() as td:
    db = os.path.join(td, "localized_knowledge.db")

    # -- missing DB is a complete, honest answer -----------------------------
    st = db_status(db)
    check("missing db: exists False", st["exists"] is False)
    check("missing db: all fields present",
          st["pages"] == 0 and st["versions"] == {} and st["sources"] == {}
          and st["pending"] == {"queued": 0, "error": 0, "done": 0})

    # -- populated DB ----------------------------------------------------------
    con = sqlite3.connect(db)
    con.execute("""CREATE TABLE knowledge_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT, topic_tag TEXT NOT NULL,
        content_payload TEXT NOT NULL, source_url TEXT NOT NULL,
        scraped_at TEXT NOT NULL, game_version_tag TEXT DEFAULT 'Patch 0.5.4')""")
    con.execute("""CREATE TABLE crawl_state (
        url TEXT PRIMARY KEY, status TEXT NOT NULL, fetched_at TEXT)""")
    rows = [
        ("mods", "x", "https://poe2db.tw/us/a", "2026-07-01T10:00:00", "Patch 0.5.4"),
        ("mods", "y", "https://poe2db.tw/us/b", "2026-07-09T09:00:00", "Patch 0.5.4"),
        ("wiki", "z", "https://www.poe2wiki.net/wiki/c", "2026-07-05T08:00:00",
         "Patch 0.5.3"),
    ]
    con.executemany("INSERT INTO knowledge_ledger (topic_tag, content_payload,"
                    " source_url, scraped_at, game_version_tag) VALUES "
                    "(?,?,?,?,?)", rows)
    con.executemany("INSERT INTO crawl_state VALUES (?,?,?)", [
        ("u1", "queued", None), ("u2", "queued", None),
        ("u3", "error", None), ("u4", "done", "t")])
    con.commit()
    con.close()

    st = db_status(db)
    check("pages counted", st["pages"] == 3)
    check("size read", st["size_bytes"] > 0)
    check("last sync is the max", st["last_scraped"] == "2026-07-09T09:00:00")
    check("versions histogram", st["versions"] == {"Patch 0.5.4": 2,
                                                   "Patch 0.5.3": 1})
    check("source domains", st["sources"] == {"poe2db.tw": 2,
                                              "www.poe2wiki.net": 1})
    check("pending split", st["pending"] == {"queued": 2, "error": 1,
                                             "done": 1})

    # -- ledger without crawl_state (old seed DBs) ------------------------------
    db2 = os.path.join(td, "seed.db")
    con = sqlite3.connect(db2)
    con.execute("CREATE TABLE knowledge_ledger (id INTEGER PRIMARY KEY, "
                "topic_tag TEXT, content_payload TEXT, source_url TEXT, "
                "scraped_at TEXT, game_version_tag TEXT)")
    con.commit()
    con.close()
    st2 = db_status(db2)
    check("no crawl_state fails soft",
          st2["pages"] == 0 and st2["pending"]["queued"] == 0)

    # -- junk file isn't a crash --------------------------------------------------
    db3 = os.path.join(td, "junk.db")
    with open(db3, "wb") as f:
        f.write(b"this is not sqlite")
    st3 = db_status(db3)
    check("corrupt file fails soft", st3["exists"] and st3["pages"] == 0)

    # -- read-only promise: status must not create/modify files -------------------
    before = os.path.getmtime(db)
    db_status(db)
    check("read-only access", os.path.getmtime(db) == before)

    # -- the window's wiring (source-level: the sandbox can't render Qt) ------
    _mw = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "gui_overlay", "mirror_window.py"),
        encoding="utf-8").read()
    check("sync medallion defers single-click (sync_click_timer)",
          "self.sync_click_timer.start(250)" in _mw)
    check("double-click on the sync medallion opens the DB window",
          'bid == "TopCenter"' in _mw and "self.open_db_status()" in _mw)
    check("DB window reads status + patch freshness",
          "def open_db_status" in _mw and "patch_freshness(" in _mw)
    check("DB window edits sources_enabled (the sync worker's config)",
          _mw.count('"sources_enabled"') >= 2)

# -- newer-patch check (local, no network) ------------------------------------
from datetime import datetime
from core_engine.database_handler import patch_freshness, default_db_path

now = datetime(2026, 7, 20, 12, 0, 0)
st = {"versions": {"Patch 0.5.4": 2, "Patch 0.5.3": 1},
      "last_scraped": "2026-07-19T09:00:00"}
pf = patch_freshness(st, ["0.5.3", "0.5.4", "0.5.10"], now=now)
check("data patch is the newest tag", pf["data_patch"] == "Patch 0.5.4")
check("latest patch sorts numerically (0.5.10 > 0.5.4)",
      pf["latest_patch"] == "0.5.10")
check("newer patch flagged", pf["newer_patch"] is True)
check("fresh sync not stale", pf["stale"] is False
      and 1.0 < pf["age_days"] < 1.2)
pf2 = patch_freshness(st, ["0.5.4", "0.5.2"], now=now)
check("same patch -> not newer", pf2["newer_patch"] is False)
check("letter suffix sorts after base", patch_freshness(
    {"versions": {"Patch 0.2.1": 1}}, ["0.2.1b"])["newer_patch"] is True)
pf3 = patch_freshness({"versions": {}, "last_scraped": "2026-06-01T00:00:00"},
                      [], now=now)
check("unknown patches fail soft",
      pf3["data_patch"] is None and pf3["latest_patch"] is None
      and pf3["newer_patch"] is False)
check("old sync is stale", pf3["stale"] is True)
check("junk input fails soft", patch_freshness(
    {"versions": {"???": 1}, "last_scraped": "not a date"},
    [None, "x"])["age_days"] is None)
check("empty status fails soft", patch_freshness(None)["stale"] is False)
check("default db path ends in the knowledge db",
      default_db_path().endswith("localized_knowledge.db"))

print(f"RESULT: {PASS} passed, {FAIL} failed")
print("ALL GREEN" if FAIL == 0 else "NOT GREEN")
sys.exit(1 if FAIL else 0)

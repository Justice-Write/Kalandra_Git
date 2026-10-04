"""
TESTS/SANDBOX_WRITE_CHECKS.PY — the write boundary documented in
docs/SANDBOXED-WRITES.md: every module-level write root the engine declares
must sit under `data_engine/` (relative to the project root). No network,
no Qt — pure import + path check. Run: python tests/sandbox_write_checks.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


def under_data_engine(p):
    """True when `p` (relative to the project root, or absolute) resolves
    inside <project>/data_engine/."""
    base = os.path.realpath(os.path.join(ROOT, "data_engine"))
    full = os.path.realpath(p if os.path.isabs(p) else os.path.join(ROOT, p))
    return full == base or full.startswith(base + os.sep)


from core_engine import (character_folio, death_review, grind_tracker,  # noqa: E402
                         item_art, player_profile, poe2_data_extract)

ROOTS = {
    "character_folio.CHAR_ROOT": character_folio.CHAR_ROOT,
    "death_review.DEATHS_DIR": death_review.DEATHS_DIR,
    "grind_tracker.DEFAULT_DB": grind_tracker.DEFAULT_DB,
    "item_art.ART_DIR": item_art.ART_DIR,
    "player_profile.PROFILE_PATH": player_profile.PROFILE_PATH,
    "poe2_data_extract.SCHEMA_PATH": poe2_data_extract.SCHEMA_PATH,
}
for name, path in ROOTS.items():
    check(f"{name} is under data_engine/ ({path})", under_data_engine(path))

# Negative controls for the helper itself (so a broken check can't pass).
check("'..' escape is rejected", not under_data_engine("data_engine/../main.py"))
check("sibling dir is rejected", not under_data_engine("data_engine_evil/x"))
check("absolute foreign path is rejected", not under_data_engine(os.path.join(ROOT, "core_engine")))

print(f"RESULT: {PASS} passed, {FAIL} failed")
print("ALL GREEN" if FAIL == 0 else "NOT GREEN")
sys.exit(1 if FAIL else 0)

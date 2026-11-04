"""Reset the working database: copy data/campus_customs.db over data/campus_customs_new.db.

Shop rule: reset to the original values before a full run. This also clears the board tables the
tools create (drafts, approval_requests, building_requests). The original file is only read, and
its checksum is printed before and after to prove it.

Run from hw5/:  python scripts/reset_db.py
"""

import hashlib
import shutil
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
ORIGINAL = DATA / "campus_customs.db"
WORKING = DATA / "campus_customs_new.db"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def reset() -> str:
    before = sha(ORIGINAL)
    for side in ("-journal", "-wal", "-shm"):
        Path(str(WORKING) + side).unlink(missing_ok=True)
    shutil.copyfile(ORIGINAL, WORKING)
    assert sha(ORIGINAL) == before, "the original changed"
    assert sha(WORKING) == before, "the copy doesn't match the original"
    return before


if __name__ == "__main__":
    digest = reset()
    print(f"Reset: campus_customs_new.db is a fresh copy of campus_customs.db (SHA-256 {digest[:8]}…{digest[-5:]}).")

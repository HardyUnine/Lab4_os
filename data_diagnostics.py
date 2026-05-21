import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
EXT4_DIR = BASE_DIR / "out_fixed" / "ext4"
XFS_DIR  = BASE_DIR / "out_fixed" / "xfs"

def diagnose(directory: Path):
    print(f"\n=== {directory} ===")
    for path in sorted(directory.glob("*.log")):
        print(f"\n-- {path.name} --")
        with path.open() as f:
            rows = list(csv.reader(f))
        if len(rows) < 2:
            print("  SKIPPED: fewer than 2 rows")
            continue

        header = rows[0]
        last   = rows[-1]
        col_idx = {name: i for i, name in enumerate(header)}

        # Print every column that contains "create"
        for col in header:
            if "create" in col.lower():
                val = last[col_idx[col]]
                print(f"  {col!r:35s} = {val!r}")

diagnose(EXT4_DIR)
diagnose(XFS_DIR)
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
EXT4_DIR = BASE_DIR / "out_fixed" / "ext4"
XFS_DIR  = BASE_DIR / "out_fixed" / "xfs"

## THIS IS KINDA USELESS, WE CAN PROBABLY DELETE IT 
def parse_last_row(path: Path):
    with path.open() as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 2:
        return None

    header = rows[0]
    last = rows[-1]

    col_idx = {name: i for i, name in enumerate(header)}

    def get(col):
        val = last[col_idx[col]]
        if val in ("", "+++++"):
            return None
        return val

    def get_float(col):
        val = get(col)
        if val is None:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    return {
        "file_size": last[col_idx["file_size"]],
        "put_block": get_float("put_block"),
        "put_block_latency": get("put_block_latency"),
        "get_block": get_float("get_block"),
        "get_block_latency": get("get_block_latency"),
    }


def parse_latency_us(lat_str: str):
    if not lat_str or lat_str == "-":
        return None
    s = lat_str.strip()
    if s.endswith("us"):
        return float(s[:-2])
    if s.endswith("ms"):
        return float(s[:-2]) * 1000.0
    try:
        return float(s)
    except ValueError:
        return None


def summarize_fs(fs_name: str, directory: Path):
    rows = []
    for path in sorted(directory.glob("*.log")):
        parsed = parse_last_row(path)
        if not parsed:
            continue
        size = parsed["file_size"]
        pb = parsed["put_block"]
        pbl_us = parse_latency_us(parsed["put_block_latency"])
        rows.append((size, pb, pbl_us))

    print(f"{fs_name}: file_size  put_block_MBps  put_block_latency_us")
    for size, pb, pbl in rows:
        pb_str = f"{pb:8.1f}" if pb is not None else "   -    "
        pbl_str = f"{pbl:10.1f}" if pbl is not None else "    -    "
        print(f"{size:>6}  {pb_str}  {pbl_str}")
    print()


def main():
    summarize_fs("ext4", EXT4_DIR)
    summarize_fs("xfs",  XFS_DIR)


if __name__ == "__main__":
    main()
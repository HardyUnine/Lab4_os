import csv
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).parent
DISK_DIR = BASE_DIR / "out_fixed" / "xfs"   # /mnt (SSD)
SHM_DIR  = BASE_DIR / "out_fixed" / "xfs_2"   # /dev/shm (RAM)


def parse_last_row(path: Path):
    with path.open() as f:
        rows = list(csv.reader(f))

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
        "seeks": get_float("seeks"),
        "seeks_latency": get("seeks_latency"),
    }


def latency_to_us(lat_str: str):
    if not lat_str:
        return None
    s = lat_str.strip()
    if s.endswith("us"):
        s = s[:-2]
        factor = 1.0
    elif s.endswith("ms"):
        s = s[:-2]
        factor = 1000.0
    else:
        factor = 1.0
    try:
        return float(s) * factor
    except ValueError:
        return None


def load_env(directory: Path):
    sizes = []
    put_block = []
    put_block_lat = []
    get_block = []
    get_block_lat = []
    seeks = []
    seeks_lat = []

    for path in sorted(directory.glob("*.log")):
        parsed = parse_last_row(path)
        if not parsed:
            continue

        sizes.append(parsed["file_size"])

        def add(metric_list, lat_list, t_key, l_key):
            t = parsed[t_key]
            lat_raw = parsed[l_key]
            l = latency_to_us(lat_raw) if lat_raw is not None else None
            if t is not None and l is not None:
                metric_list.append(t)
                lat_list.append(l)

        add(put_block, put_block_lat, "put_block", "put_block_latency")
        add(get_block, get_block_lat, "get_block", "get_block_latency")
        add(seeks, seeks_lat, "seeks", "seeks_latency")

    return {
        "sizes": sizes,
        "put_block": put_block,
        "put_block_lat": put_block_lat,
        "get_block": get_block,
        "get_block_lat": get_block_lat,
        "seeks": seeks,
        "seeks_lat": seeks_lat,
    }


def scatter_tp_vs_lat(disk_vals, shm_vals, key_tp, key_lat,
                      title, tp_label, lat_label, filename=None):
    plt.figure(figsize=(6, 4))
    plt.scatter(
        disk_vals[key_tp],
        disk_vals[key_lat],
        marker="o",
        color="tab:blue",
        label="xfs on disk (/mnt)",
    )
    plt.scatter(
        shm_vals[key_tp],
        shm_vals[key_lat],
        marker="s",
        color="tab:orange",
        label="xfs on /dev/shm",
    )
    plt.xlabel(tp_label)
    plt.ylabel(lat_label)
    plt.title(title)
    plt.grid(True, which="both", linestyle="--", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=150)


def main():
    disk = load_env(DISK_DIR)
    shm  = load_env(SHM_DIR)

    # Sequential write
    scatter_tp_vs_lat(
        disk,
        shm,
        "put_block",
        "put_block_lat",
        "Sequential write: xfs disk vs /dev/shm",
        "put_block throughput (MB/s)",
        "put_block latency (µs)",
        filename="task2_xfs_write_tp_lat.png",
    )

    # Sequential read
    scatter_tp_vs_lat(
        disk,
        shm,
        "get_block",
        "get_block_lat",
        "Sequential read: xfs disk vs /dev/shm",
        "get_block throughput (MB/s)",
        "get_block latency (µs)",
        filename="task2_xfs_read_tp_lat.png",
    )

    # Seeks (if present)
    scatter_tp_vs_lat(
        disk,
        shm,
        "seeks",
        "seeks_lat",
        "Random seeks: xfs disk vs /dev/shm",
        "seeks (ops/s)",
        "seeks latency (µs)",
        filename="task2_xfs_seeks_tp_lat.png",
    )

    plt.show()


if __name__ == "__main__":
    main()
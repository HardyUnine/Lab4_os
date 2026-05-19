import csv
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).parent
EXT4_DIR = BASE_DIR / "out_fixed" / "ext4"
XFS_DIR  = BASE_DIR / "out_fixed" / "xfs"


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
        # header has "file_size"
        "file_size": last[col_idx["file_size"]],

        # sequential write / read
        # headers: put_block, put_block_latency, get_block, get_block_latency
        "put_block": get_float("put_block"),
        "put_block_latency": get("put_block_latency"),
        "get_block": get_float("get_block"),
        "get_block_latency": get("get_block_latency"),

        # seeks
        # headers: seeks, seeks_latency
        "seeks": get_float("seeks"),
        "seeks_latency": get("seeks_latency"),

        # creation
        # headers: seq_create, seq_create_latency, ran_create, ran_create_latency
        "seq_create": get_float("seq_create"),
        "seq_create_latency": get("seq_create_latency"),
        "ran_create": get_float("ran_create"),
        "ran_create_latency": get("ran_create_latency"),
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


def load_fs(directory: Path):
    sizes = []
    put_block = []
    put_block_lat = []
    get_block = []
    get_block_lat = []
    seeks = []
    seeks_lat = []
    seq_create = []
    seq_create_lat = []
    ran_create = []
    ran_create_lat = []

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
        add(seq_create, seq_create_lat, "seq_create", "seq_create_latency")
        add(ran_create, ran_create_lat, "ran_create", "ran_create_latency")

    return {
        "sizes": sizes,
        "put_block": put_block,
        "put_block_lat": put_block_lat,
        "get_block": get_block,
        "get_block_lat": get_block_lat,
        "seeks": seeks,
        "seeks_lat": seeks_lat,
        "seq_create": seq_create,
        "seq_create_lat": seq_create_lat,
        "ran_create": ran_create,
        "ran_create_lat": ran_create_lat,
    }


def scatter_tp_vs_lat(ext4_vals, xfs_vals, key_tp, key_lat,
                      title, tp_label, lat_label, filename=None):
    plt.figure(figsize=(6, 4))
    plt.scatter(
        ext4_vals[key_tp],
        ext4_vals[key_lat],
        marker="o",
        color="tab:blue",
        label="ext4",
    )
    plt.scatter(
        xfs_vals[key_tp],
        xfs_vals[key_lat],
        marker="s",
        color="tab:orange",
        label="xfs",
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
    ext4 = load_fs(EXT4_DIR)
    xfs = load_fs(XFS_DIR)

    # 1) Sequential write
    scatter_tp_vs_lat(
        ext4,
        xfs,
        "put_block",
        "put_block_lat",
        "Sequential write: throughput vs latency",
        "put_block throughput (MB/s)",
        "put_block latency (µs)",
        filename="write_tp_lat.png",
    )

    # 2) Sequential read
    scatter_tp_vs_lat(
        ext4,
        xfs,
        "get_block",
        "get_block_lat",
        "Sequential read: throughput vs latency",
        "get_block throughput (MB/s)",
        "get_block latency (µs)",
        filename="read_tp_lat.png",
    )

    # 3) Random seeks
    scatter_tp_vs_lat(
        ext4,
        xfs,
        "seeks",
        "seeks_lat",
        "Random seeks: throughput vs latency",
        "seeks (ops/s)",
        "seeks latency (µs)",
        filename="seeks_tp_lat.png",
    )

    # 4) Sequential create
    scatter_tp_vs_lat(
        ext4,
        xfs,
        "seq_create",
        "seq_create_lat",
        "Sequential create: throughput vs latency",
        "seq_create (files/s)",
        "seq_create latency (µs)",
        filename="seq_create_tp_lat.png",
    )

    # 5) Random create
    scatter_tp_vs_lat(
        ext4,
        xfs,
        "ran_create",
        "ran_create_lat",
        "Random create: throughput vs latency",
        "ran_create (files/s)",
        "ran_create latency (µs)",
        filename="ran_create_tp_lat.png",
    )

    plt.show()


if __name__ == "__main__":
    main()
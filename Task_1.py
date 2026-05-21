import csv
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent
EXT4_DIR = BASE_DIR / "out_fixed" / "ext4"
XFS_DIR = BASE_DIR / "out_fixed" / "xfs"


# reads the last row of a bonnie++ csv log
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
        # seq_create throughput is always empty in our logs
        "seq_create_latency": get("seq_create_latency"),
        "ran_create": get_float("ran_create"),
        "ran_create_latency": get("ran_create_latency"),
    }


# converts bonnie++ latency strings like "306us" or "14ms" to microseconds
def latency_to_us(lat_str):
    if not lat_str:
        return None
    s = lat_str.strip()
    if s.endswith("us"):
        return float(s[:-2])
    elif s.endswith("ms"):
        return float(s[:-2]) * 1000.0
    try:
        return float(s)
    except ValueError:
        return None


def load_fs(directory):
    sizes = []
    put_block = []; put_block_lat = []
    get_block = []; get_block_lat = []
    seeks = []; seeks_lat = []
    seq_create_lat = []
    ran_create = []; ran_create_lat = []

    metrics = [
        (put_block, put_block_lat, "put_block", "put_block_latency"),
        (get_block, get_block_lat, "get_block", "get_block_latency"),
        (seeks, seeks_lat, "seeks", "seeks_latency"),
        (ran_create, ran_create_lat, "ran_create", "ran_create_latency"),
    ]

    for path in sorted(directory.glob("*.log")):
        parsed = parse_last_row(path)
        if not parsed:
            continue

        sizes.append(parsed["file_size"])

        for ml, ll, tk, lk in metrics:
            t = parsed[tk]
            l = latency_to_us(parsed[lk]) if parsed[lk] is not None else None
            if t is not None and l is not None:
                ml.append(t)
                ll.append(l)

        # seq_create has no throughput so we just grab latency
        l = latency_to_us(parsed["seq_create_latency"]) if parsed["seq_create_latency"] else None
        if l is not None:
            seq_create_lat.append(l)

    return {
        "sizes": sizes,
        "put_block": put_block, "put_block_lat": put_block_lat,
        "get_block": get_block, "get_block_lat": get_block_lat,
        "seeks": seeks, "seeks_lat": seeks_lat,
        "seq_create_lat": seq_create_lat,
        "ran_create": ran_create, "ran_create_lat": ran_create_lat,
    }


def scatter_tp_vs_lat(vals1, vals2, key_tp, key_lat, title, tp_label, lat_label, filename=None):
    plt.figure(figsize=(6, 4))
    plt.scatter(vals1[key_tp], vals1[key_lat], marker="o", color="tab:blue", label="ext4")
    plt.scatter(vals2[key_tp], vals2[key_lat], marker="s", color="tab:orange", label="xfs")
    plt.xlabel(tp_label)
    plt.ylabel(lat_label)
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=150)


# bar chart for seq_create since bonnie++ never recorded throughput for it
def bar_seq_create_latency(ext4_vals, xfs_vals, sizes, filename=None):
    n = len(sizes)
    x = list(range(n))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([i - width/2 for i in x], ext4_vals["seq_create_lat"], width, label="ext4", color="tab:blue")
    ax.bar([i + width/2 for i in x], xfs_vals["seq_create_lat"], width, label="xfs", color="tab:orange")
    ax.set_xticks(x)
    ax.set_xticklabels(sizes)
    ax.set_xlabel("File size")
    ax.set_ylabel("seq_create latency (µs)")
    ax.set_title("Sequential create latency by file size")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend()
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=150)


def main():
    ext4 = load_fs(EXT4_DIR)
    xfs = load_fs(XFS_DIR)

    sizes = ["64M", "128M", "256M", "512M", "1G", "2G"]

    scatter_tp_vs_lat(ext4, xfs, "put_block", "put_block_lat",
        "Sequential write: throughput vs latency",
        "put_block throughput (MB/s)", "put_block latency (µs)",
        filename="write_tp_lat.png")

    scatter_tp_vs_lat(ext4, xfs, "get_block", "get_block_lat",
        "Sequential read: throughput vs latency",
        "get_block throughput (MB/s)", "get_block latency (µs)",
        filename="read_tp_lat.png")

    scatter_tp_vs_lat(ext4, xfs, "seeks", "seeks_lat",
        "Random seeks: throughput vs latency",
        "seeks (ops/s)", "seeks latency (µs)",
        filename="seeks_tp_lat.png")

    bar_seq_create_latency(ext4, xfs, sizes=sizes, filename="seq_create_tp_lat.png")

    scatter_tp_vs_lat(ext4, xfs, "ran_create", "ran_create_lat",
        "Random create: throughput vs latency",
        "ran_create (files/s)", "ran_create latency (µs)",
        filename="ran_create_tp_lat.png")

    plt.show()


if __name__ == "__main__":
    main()
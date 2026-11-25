#!/usr/bin/env python3
"""
TD-08: bikin ground truth jumlah orang dari anotasi SCUT-HEAD Part A (format Pascal VOC XML).

Output:
  gt_counts.csv         -> semua gambar di split (image_id, gt_count, bin)
  gt_counts_subset.csv  -> subset berlapis sepi/sedang/ramai (untuk "min. 100 gambar" di backlog)

Contoh:
  python prepare_gt.py --ann-dir SCUT-HEAD/PartA/Annotations \
                       --split-file test.txt --out-dir data/
"""
import argparse
import csv
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BINS = ["sepi", "sedang", "ramai"]


def read_ids(split_file: Path) -> list[str]:
    # File split berformat CRLF -> wajib strip, dan buang baris kosong.
    with open(split_file, encoding="utf-8") as f:
        ids = [line.strip() for line in f if line.strip()]
    if len(ids) != len(set(ids)):
        print("PERINGATAN: ada ID duplikat di split file", file=sys.stderr)
    return ids


def count_heads(xml_path: Path) -> tuple[int, int]:
    """Return (jumlah_objek, jumlah_difficult). Setiap <object> = 1 kepala (label 'person')."""
    root = ET.parse(xml_path).getroot()
    total = difficult = 0
    for obj in root.findall("object"):
        total += 1
        d = obj.findtext("difficult", default="0").strip()
        if d == "1":
            difficult += 1
    return total, difficult


def assign_bins(rows: list[dict]) -> None:
    """Bagi 3 kelompok sama besar berdasar urutan gt_count (rank-based, aman untuk nilai kembar)."""
    ordered = sorted(rows, key=lambda r: (r["gt_count"], r["image_id"]))
    n = len(ordered)
    for i, r in enumerate(ordered):
        r["bin"] = BINS[min(i * 3 // n, 2)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ann-dir", required=True, type=Path, help="folder berisi PartA_xxxxx.xml")
    ap.add_argument("--split-file", required=True, type=Path, help="mis. test.txt")
    ap.add_argument("--out-dir", default=Path("data"), type=Path)
    ap.add_argument("--per-bin", default=35, type=int, help="gambar per kelompok untuk subset (3x ini)")
    ap.add_argument("--seed", default=42, type=int, help="catat di README supaya reproducible")
    args = ap.parse_args()

    ids = read_ids(args.split_file)
    rows, missing = [], []
    for image_id in ids:
        xml_path = args.ann_dir / f"{image_id}.xml"
        if not xml_path.exists():
            missing.append(image_id)
            continue
        total, difficult = count_heads(xml_path)
        rows.append({"image_id": image_id, "gt_count": total, "n_difficult": difficult})

    if missing:
        print(f"PERINGATAN: {len(missing)} anotasi tidak ditemukan, contoh: {missing[:3]}", file=sys.stderr)
    if not rows:
        sys.exit("Tidak ada anotasi terbaca. Cek --ann-dir.")

    assign_bins(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    fields = ["image_id", "gt_count", "bin", "n_difficult"]
    full_path = args.out_dir / "gt_counts.csv"
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["image_id"]))

    rng = random.Random(args.seed)
    subset = []
    for b in BINS:
        pool = [r for r in rows if r["bin"] == b]
        subset += rng.sample(pool, min(args.per_bin, len(pool)))
    subset_path = args.out_dir / "gt_counts_subset.csv"
    with open(subset_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(subset, key=lambda r: r["image_id"]))

    # Ringkasan untuk README / proposal
    print(f"Split           : {args.split_file.name} ({len(ids)} id, {len(rows)} anotasi terbaca)")
    for b in BINS:
        c = [r["gt_count"] for r in rows if r["bin"] == b]
        if not c:
            continue
        print(f"  {b:7s}: {len(c):4d} gambar, gt_count {min(c)}-{max(c)}")
    print(f"Subset          : {len(subset)} gambar (seed={args.seed})")
    print(f"Ditulis         : {full_path}, {subset_path}")


if __name__ == "__main__":
    main()

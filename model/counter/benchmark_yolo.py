#!/usr/bin/env python3
"""
TD-06 mode uji + DS-08: hitung jumlah 'person' dengan YOLO pretrained, bandingkan ke ground truth.

Input : gt_counts.csv / gt_counts_subset.csv (dari prepare_gt.py) + folder JPEGImages
Output: results/pred_counts_<model>_<imgsz>.csv  (image_id, pred_count)
        results/summary.csv                      (metrik per model x imgsz x kelompok)

Contoh (mulai dari subset dulu):
  python counter\\benchmark_yolo.py --img-dir SCUT_HEAD_Part_A\\JPEGImages ^
         --gt-csv data\\gt_counts_subset.csv --out-dir results
"""
import argparse
import csv
import statistics
import time
from pathlib import Path


def read_gt(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["gt_count"] = int(r["gt_count"])
    return rows


def compute_metrics(gt: dict[str, int], pred: dict[str, int], ids: list[str]) -> dict:
    """MAE, MAPE (hanya gt>0), bias (pred - gt; negatif = undercount), RMSE."""
    errs = [pred[i] - gt[i] for i in ids]
    abs_errs = [abs(e) for e in errs]
    pct = [abs(pred[i] - gt[i]) / gt[i] * 100 for i in ids if gt[i] > 0]
    return {
        "n": len(ids),
        "mae": statistics.fmean(abs_errs),
        "mape_%": statistics.fmean(pct) if pct else float("nan"),
        "bias": statistics.fmean(errs),
        "rmse": statistics.fmean(e * e for e in errs) ** 0.5,
        "mean_gt": statistics.fmean(gt[i] for i in ids),
    }


def run_model(model, ids, img_dir: Path, imgsz: int, conf: float, device):
    preds = {}
    for k, image_id in enumerate(ids, 1):
        img_path = img_dir / f"{image_id}.jpg"
        if not img_path.exists():
            raise FileNotFoundError(img_path)
        r = model.predict(
            str(img_path), classes=[0], conf=conf, imgsz=imgsz,
            max_det=1000, device=device, verbose=False,
        )[0]
        preds[image_id] = len(r.boxes)
        if k % 25 == 0 or k == len(ids):
            print(f"    {k}/{len(ids)}", end="\r", flush=True)
    print()
    return preds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--img-dir", required=True, type=Path)
    ap.add_argument("--gt-csv", required=True, type=Path)
    ap.add_argument("--out-dir", default=Path("results"), type=Path)
    ap.add_argument("--models", nargs="+",
                    default=["yolo26n.pt", "yolo26s.pt", "yolo26m.pt", "yolo26l.pt"])
    ap.add_argument("--imgsz", nargs="+", type=int, default=[640, 960, 1280])
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--device", default=None, help="mis. cpu, 0 (GPU pertama). Kosong = otomatis")
    args = ap.parse_args()

    from ultralytics import YOLO  # impor di sini agar compute_metrics bisa dites tanpa ultralytics
    import ultralytics

    rows = read_gt(args.gt_csv)
    ids = [r["image_id"] for r in rows]
    gt = {r["image_id"]: r["gt_count"] for r in rows}
    bins = {r["image_id"]: r.get("bin", "semua") for r in rows}
    bin_names = [b for b in ("sepi", "sedang", "ramai") if b in set(bins.values())]
    print(f"{len(ids)} gambar | ultralytics {ultralytics.__version__} | conf={args.conf}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for name in args.models:
        model = YOLO(name)  # unduh otomatis pertama kali
        for imgsz in args.imgsz:
            print(f"  {name} @ {imgsz}")
            t0 = time.time()
            pred = run_model(model, ids, args.img_dir, imgsz, args.conf, args.device)
            sec_per_img = (time.time() - t0) / len(ids)

            tag = f"{Path(name).stem}_{imgsz}"
            with open(args.out_dir / f"pred_counts_{tag}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(["image_id", "pred_count"])
                for i in ids:
                    w.writerow([i, pred[i]])

            groups = [("semua", ids)] + [(b, [i for i in ids if bins[i] == b]) for b in bin_names]
            for gname, gids in groups:
                m = compute_metrics(gt, pred, gids)
                summary.append({"model": Path(name).stem, "imgsz": imgsz, "conf": args.conf,
                                "kelompok": gname, "sec_per_img": round(sec_per_img, 3),
                                **{k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()}})

    fields = ["model", "imgsz", "conf", "kelompok", "n", "mean_gt", "mae", "mape_%", "bias", "rmse", "sec_per_img"]
    out = args.out_dir / "summary.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(summary)

    print("\nRingkasan (semua gambar), diurutkan dari MAE terkecil:")
    print(f"{'model':12s} {'imgsz':>5s} {'MAE':>7s} {'MAPE%':>7s} {'bias':>8s} {'s/img':>6s}")
    for s in sorted((s for s in summary if s["kelompok"] == "semua"), key=lambda s: s["mae"]):
        print(f"{s['model']:12s} {s['imgsz']:5d} {s['mae']:7.2f} {s['mape_%']:7.1f} {s['bias']:8.2f} {s['sec_per_img']:6.2f}")
    print(f"\nLengkap per kelompok: {out}")


if __name__ == "__main__":
    main()

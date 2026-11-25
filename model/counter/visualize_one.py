#!/usr/bin/env python3
"""
Gambar bukti untuk proposal: anotasi kepala (ground truth) vs deteksi YOLO pada satu gambar.

Output PNG dua panel:
  kiri  = ground truth (kotak hijau = tiap kepala yang dianotasi)
  kanan = hasil YOLO (kotak merah = deteksi 'person').
          Titik pusat kepala GT diberi tanda:
            hijau  = pusat kepala jatuh di dalam salah satu kotak YOLO (tertangkap)
            kuning = tidak ada kotak YOLO yang menutupinya (terlewat)
          Kotak YOLO tanpa kepala GT di dalamnya digambar oranye (kandidat false positive
          atau orang yang tidak dianotasi).

CATATAN: pencocokan 'tertangkap/terlewat' hanya heuristik visual (pusat kepala di dalam kotak YOLO),
BUKAN metrik resmi. Metrik resmi tetap MAE/MAPE/bias dari benchmark_yolo.py.

Contoh:
  python counter\\visualize_one.py PartA_01999 PartA_00595 ^
      --ann-dir SCUT_HEAD_Part_A\\Annotations --img-dir SCUT_HEAD_Part_A\\JPEGImages
  python counter\\visualize_one.py --worst 5 --gt-csv data\\gt_counts.csv ^
      --pred-csv results_final_test\\pred_counts_yolo26l_1280.csv ^
      --ann-dir SCUT_HEAD_Part_A\\Annotations --img-dir SCUT_HEAD_Part_A\\JPEGImages
"""
import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

GREEN = (60, 180, 60)      # BGR
RED = (50, 50, 230)
YELLOW = (0, 220, 255)
ORANGE = (0, 140, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def load_gt_boxes(xml_path: Path) -> list[tuple[int, int, int, int]]:
    root = ET.parse(xml_path).getroot()
    boxes = []
    for obj in root.findall("object"):
        bb = obj.find("bndbox")
        if bb is None:
            continue
        boxes.append(tuple(int(float(bb.findtext(k))) for k in ("xmin", "ymin", "xmax", "ymax")))
    return boxes


def predict_boxes(model, img_path: Path, imgsz: int, conf: float):
    r = model.predict(str(img_path), classes=[0], conf=conf, imgsz=imgsz,
                      max_det=1000, verbose=False)[0]
    xyxy = r.boxes.xyxy.cpu().numpy() if len(r.boxes) else np.zeros((0, 4))
    scores = r.boxes.conf.cpu().numpy() if len(r.boxes) else np.zeros((0,))
    return xyxy, scores


def classify(gt_boxes, pred_xyxy):
    """Heuristik: kepala GT 'tertangkap' bila pusatnya ada di dalam >=1 kotak prediksi."""
    captured, missed = [], []
    for (x1, y1, x2, y2) in gt_boxes:
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        hit = any(p[0] <= cx <= p[2] and p[1] <= cy <= p[3] for p in pred_xyxy)
        (captured if hit else missed).append((x1, y1, x2, y2))
    unmatched_pred = []
    for p in pred_xyxy:
        has_head = any(p[0] <= (g[0] + g[2]) / 2 <= p[2] and p[1] <= (g[1] + g[3]) / 2 <= p[3]
                       for g in gt_boxes)
        if not has_head:
            unmatched_pred.append(p)
    return captured, missed, unmatched_pred


def put_label(img, text, org, scale=0.7, color=WHITE, bg=BLACK):
    (w, h), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
    x, y = org
    cv2.rectangle(img, (x, y - h - base), (x + w + 6, y + base), bg, -1)
    cv2.putText(img, text, (x + 3, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2, cv2.LINE_AA)


def draw(img, gt_boxes, pred_xyxy, scores, title):
    h, w = img.shape[:2]
    thick = max(1, round(w / 700))
    captured, missed, unmatched = classify(gt_boxes, pred_xyxy)

    left = img.copy()
    for (x1, y1, x2, y2) in gt_boxes:
        cv2.rectangle(left, (x1, y1), (x2, y2), GREEN, thick)

    right = img.copy()
    for p in pred_xyxy:
        cv2.rectangle(right, tuple(int(v) for v in p[:2]), tuple(int(v) for v in p[2:]), RED, thick)
    for p in unmatched:
        cv2.rectangle(right, tuple(int(v) for v in p[:2]), tuple(int(v) for v in p[2:]), ORANGE, thick + 1)
    r = max(3, w // 250)
    for (x1, y1, x2, y2) in captured:
        cv2.circle(right, ((x1 + x2) // 2, (y1 + y2) // 2), r, GREEN, -1)
    for (x1, y1, x2, y2) in missed:
        cv2.circle(right, ((x1 + x2) // 2, (y1 + y2) // 2), r + 1, YELLOW, -1)
        cv2.circle(right, ((x1 + x2) // 2, (y1 + y2) // 2), r + 1, BLACK, 1)

    put_label(left, f"Ground truth: {len(gt_boxes)} kepala", (10, 30))
    put_label(right, f"YOLO: {len(pred_xyxy)} deteksi | tertangkap {len(captured)}/{len(gt_boxes)}, "
                     f"terlewat {len(missed)}", (10, 30))

    sep = np.full((h, 6, 3), 255, np.uint8)
    body = np.hstack([left, sep, right])
    bar_h = 44
    bar = np.full((bar_h, body.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, BLACK, 2, cv2.LINE_AA)
    legend_y = body.shape[0] + bar_h - 14
    out = np.vstack([bar, body])
    # legenda kecil di bawah panel kanan
    lx = left.shape[1] + 20
    for label, col in (("tertangkap", GREEN), ("terlewat", YELLOW), ("kotak YOLO", RED),
                       ("YOLO tanpa GT", ORANGE)):
        cv2.circle(out, (lx, out.shape[0] - 18), 7, col, -1)
        cv2.putText(out, label, (lx + 14, out.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    WHITE, 2, cv2.LINE_AA)
        cv2.putText(out, label, (lx + 14, out.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    BLACK, 1, cv2.LINE_AA)
        lx += 40 + 9 * len(label)
    return out, (len(captured), len(missed), len(unmatched))


def pick_worst(gt_csv: Path, pred_csv: Path, n: int) -> list[str]:
    def read(p, key):
        with open(p, newline="", encoding="utf-8") as f:
            return {r["image_id"]: int(r[key]) for r in csv.DictReader(f)}
    gt, pred = read(gt_csv, "gt_count"), read(pred_csv, "pred_count")
    ids = [i for i in gt if i in pred]
    ids.sort(key=lambda i: abs(pred[i] - gt[i]), reverse=True)
    return ids[:n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image_ids", nargs="*", help="mis. PartA_01999 (tanpa ekstensi)")
    ap.add_argument("--ann-dir", required=True, type=Path)
    ap.add_argument("--img-dir", required=True, type=Path)
    ap.add_argument("--out-dir", default=Path("figures"), type=Path)
    ap.add_argument("--model", default="yolo26l.pt")
    ap.add_argument("--imgsz", type=int, default=1280)
    ap.add_argument("--conf", type=float, default=0.05)
    ap.add_argument("--worst", type=int, default=0, help="ambil N gambar dengan selisih terbesar")
    ap.add_argument("--gt-csv", type=Path)
    ap.add_argument("--pred-csv", type=Path)
    args = ap.parse_args()

    ids = list(args.image_ids)
    if args.worst:
        if not (args.gt_csv and args.pred_csv):
            sys.exit("--worst butuh --gt-csv dan --pred-csv")
        ids += pick_worst(args.gt_csv, args.pred_csv, args.worst)
    if not ids:
        sys.exit("Beri image_id, atau pakai --worst N.")

    from ultralytics import YOLO  # impor di sini agar fungsi lain bisa dites tanpa ultralytics
    model = YOLO(args.model)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for image_id in ids:
        img_path = args.img_dir / f"{image_id}.jpg"
        xml_path = args.ann_dir / f"{image_id}.xml"
        img = cv2.imread(str(img_path))
        if img is None or not xml_path.exists():
            print(f"LEWATI {image_id}: gambar atau anotasi tidak ditemukan", file=sys.stderr)
            continue
        gt_boxes = load_gt_boxes(xml_path)
        pred_xyxy, scores = predict_boxes(model, img_path, args.imgsz, args.conf)
        title = (f"{image_id} | {Path(args.model).stem} imgsz {args.imgsz} conf {args.conf} | "
                 f"GT {len(gt_boxes)} vs YOLO {len(pred_xyxy)}")
        out, (cap, mis, unm) = draw(img, gt_boxes, pred_xyxy, scores, title)
        out_path = args.out_dir / f"{image_id}_{Path(args.model).stem}_{args.imgsz}_c{args.conf}.png"
        cv2.imwrite(str(out_path), out)
        print(f"{image_id}: GT {len(gt_boxes)}, YOLO {len(pred_xyxy)}, tertangkap {cap}, "
              f"terlewat {mis}, YOLO tanpa GT {unm} -> {out_path}")


if __name__ == "__main__":
    main()

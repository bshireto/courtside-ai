"""Embed every orange-pinnie detection so a classifier can pick out the user.

Step 1 (embed):  python orange_crops.py embed
  - every person box with an orange torso in data/tracks.jsonl
  - DINOv2 ViT-S/14 embedding of the (padded) crop -> data/orange_emb.npz
Step 2 (sheets): python orange_crops.py sheets N_PER_SHEET N_SHEETS
  - stratified sample over time, numbered grids for labelling -> SCRATCH/label/sheet_XX.jpg
    and data/label_sample.json (sheet, index -> detection row)
"""
import json, os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import bbconfig
F5 = bbconfig.F5
LABEL = _o.path.join(bbconfig.WORK, "label")


def orange_dets():
    out = []
    # game.json "plain_players": the user is not always in an orange pinnie -> keep every player-sized detection
    everyone = bbconfig.CFG.get("plain_players")
    for line in open("data/tracks.jsonl"):
        r = json.loads(line)
        for p in r["p"]:
            tid, c, x0, y0, x1, y1, orange, lime, navy, skin, dark, red = p
            if (everyone and (y1 - y0) >= 70 and c >= 0.35) or (orange >= 0.08 and lime < 0.15 and (y1 - y0) >= 40):
                out.append({"t": r["t"], "k": r["k"], "tid": tid, "box": [x0, y0, x1, y1], "col": [orange, lime, navy, skin, dark, red]})
    return out


def crop(im, box, pad=0.12):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    return im.crop((int(x0 - w * pad), int(y0 - h * pad * 0.6), int(x1 + w * pad), int(y1 + h * pad * 0.3)))


def embed():
    import torch
    torch.set_num_threads(4)
    model = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14").eval()
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    dets = [d for d in orange_dets() if d["k"] % 2 == 1]  # 2.5 fps is enough; tracks fill the rest
    json.dump(dets, open("data/orange_dets.json", "w"))  # written first so labelling sheets can be built meanwhile
    print("dets", len(dets), flush=True)
    by_k = {}
    for i, d in enumerate(dets):
        by_k.setdefault(d["k"], []).append(i)
    embs = np.zeros((len(dets), 384), np.float16)
    batch, idx = [], []

    def flush():
        if not batch:
            return
        x = torch.stack(batch)
        with torch.no_grad():
            e = model(x)
        e = torch.nn.functional.normalize(e, dim=1).numpy().astype(np.float16)
        embs[idx] = e
        batch.clear(); idx.clear()

    for n, (k, ids) in enumerate(sorted(by_k.items())):
        im = Image.open(os.path.join(F5, f"{k:05d}.jpg")).convert("RGB")
        for i in ids:
            c = crop(im, dets[i]["box"]).resize((98, 196), Image.BILINEAR)
            a = torch.from_numpy(np.asarray(c, np.float32) / 255.0).permute(2, 0, 1)
            batch.append((a - mean) / std); idx.append(i)
            if len(batch) >= 64:
                flush()
        if n % 500 == 0:
            print(n, len(by_k), flush=True)
    flush()
    np.savez_compressed("data/orange_emb.npz", emb=embs)
    json.dump(dets, open("data/orange_dets.json", "w"))
    print("done", len(dets))


def sheets(per, nsheets):
    dets = json.load(open("data/orange_dets.json"))
    random.seed(7)
    total = per * nsheets
    # stratify over time: equal quota per 20 s bucket
    buckets = {}
    for i, d in enumerate(dets):
        buckets.setdefault(int(d["t"] // 20), []).append(i)
    keys = sorted(buckets)
    quota = max(1, total // len(keys))
    pick = []
    for b in keys:
        pick += random.sample(buckets[b], min(quota, len(buckets[b])))
    rest = [i for i in range(len(dets)) if i not in set(pick)]
    pick += random.sample(rest, max(0, total - len(pick)))
    pick = pick[:total]
    random.shuffle(pick)
    os.makedirs(LABEL, exist_ok=True)
    font = ImageFont.truetype("arialbd.ttf", 22)
    TW, TH, COLS = 150, 300, 8
    sample = []
    for s in range(nsheets):
        ids = pick[s * per:(s + 1) * per]
        rows = (len(ids) + COLS - 1) // COLS
        sh = Image.new("RGB", (COLS * TW, rows * TH), "white")
        for j, i in enumerate(ids):
            d = dets[i]
            im = Image.open(os.path.join(F5, f"{d['k']:05d}.jpg")).convert("RGB")
            c = crop(im, d["box"], pad=0.25)
            sc = min((TW - 6) / c.width, (TH - 30) / c.height)
            c = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS)
            tile = Image.new("RGB", (TW, TH), (40, 40, 40))
            tile.paste(c, ((TW - c.width) // 2, (TH - c.height) // 2 + 10))
            dr = ImageDraw.Draw(tile)
            dr.rectangle([0, 0, 40, 26], fill="black")
            dr.text((3, 1), str(j), fill="yellow", font=font)
            sh.paste(tile, ((j % COLS) * TW, (j // COLS) * TH))
            sample.append({"sheet": s, "idx": j, "det": i})
        sh.save(os.path.join(LABEL, f"sheet_{s:02d}.jpg"), quality=90)
    json.dump(sample, open("data/label_sample.json", "w"))
    print("sheets", nsheets, "crops", len(sample))


if __name__ == "__main__":
    if sys.argv[1] == "embed":
        embed()
    else:
        sheets(int(sys.argv[2]), int(sys.argv[3]))

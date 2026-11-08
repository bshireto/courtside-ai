"""Group every player into identities and build a numbered photo sheet to ask names.

  python players.py embed     -> data/people_emb.npz + data/people_dets.json (all players, 1 fps, both teams)
  python players.py cluster   -> data/players_auto.json + WORK/players_sheet.jpg (numbered, 6 crops each)
  python players.py name '{"3": "Barak", "7": "Tomer", ...}'
                              -> data/players.json (id -> name, team, photo) and updates PIPELINE/players/known.json

Tracklets (ByteTrack ids) are the unit: their mean DINOv2 embedding is clustered per team colour with
agglomerative clustering (cosine). Known players from earlier games (PIPELINE/players/known.json, mean
embeddings) are matched first so they come back already named.
"""
import json, os, sys, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

KNOWN = os.path.join(bbconfig.PIPELINE, "players", "known.json")


def team_of(col):
    orange, lime = col[0], col[1]
    if orange >= 0.10 and orange > lime:
        return "orange"
    if lime >= 0.10:
        return "lime"
    return None


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
    dets = []
    for line in open(bbconfig.data("tracks.jsonl")):
        r = json.loads(line)
        if r["k"] % 5 != 1:  # 1 fps
            continue
        for p in r["p"]:
            tid, c, x0, y0, x1, y1, *col = p
            # "plain" = no pinnie colour on the torso (a game without pinnies, or a pinnie rolled around the neck)
            tm = team_of(col) or ("plain" if bbconfig.CFG.get("plain_players") else None)
            if tm and (y1 - y0) >= 90 and c >= 0.5:
                dets.append({"t": r["t"], "k": r["k"], "tid": tid, "setup": bbconfig.setup_of(r["t"]), "box": [x0, y0, x1, y1], "team": tm})
    print("dets", len(dets), flush=True)
    embs = np.zeros((len(dets), 384), np.float32)
    by_k = collections.defaultdict(list)
    for i, d in enumerate(dets):
        by_k[d["k"]].append(i)
    batch, idx = [], []

    def flush():
        if batch:
            with torch.no_grad():
                e = torch.nn.functional.normalize(model(torch.stack(batch)), dim=1).numpy()
            embs[idx] = e
            batch.clear(); idx.clear()

    for k, ids in sorted(by_k.items()):
        im = Image.open(os.path.join(bbconfig.F5, f"{k:05d}.jpg")).convert("RGB")
        for i in ids:
            a = np.asarray(crop(im, dets[i]["box"]).resize((98, 196), Image.BILINEAR), np.float32) / 255.0
            # blank the pinnie (torso) so identity comes from head, sleeves, shorts, legs and shoes
            a = a.copy(); a[int(196 * 0.24):int(196 * 0.52), int(98 * 0.22):int(98 * 0.78)] = 0.5
            batch.append((torch.from_numpy(a).permute(2, 0, 1) - mean) / std); idx.append(i)
            if len(batch) >= 64:
                flush()
    flush()
    np.savez_compressed(bbconfig.data("people_emb.npz"), emb=embs)
    json.dump(dets, open(bbconfig.data("people_dets.json"), "w"))
    print("done")


def cluster(dist=0.35, min_secs=40):
    from sklearn.cluster import AgglomerativeClustering
    dets = json.load(open(bbconfig.data("people_dets.json")))
    E = np.load(bbconfig.data("people_emb.npz"))["emb"]
    known = json.load(open(KNOWN)) if os.path.exists(KNOWN) else {}
    players = []
    for team in ("orange", "lime"):
        tr = collections.defaultdict(list)
        for i, d in enumerate(dets):
            if d["team"] == team and d["tid"] >= 0:
                tr[(d["setup"], d["tid"])].append(i)
        keys = [k for k, v in tr.items() if len(v) >= 3]
        if len(keys) < 2:
            continue
        M = np.stack([E[tr[k]].mean(0) for k in keys])
        M /= np.linalg.norm(M, axis=1, keepdims=True)
        lab = AgglomerativeClustering(n_clusters=None, distance_threshold=dist, metric="cosine", linkage="average").fit_predict(M)
        for c in sorted(set(lab)):
            members = [i for k, l in zip(keys, lab) if l == c for i in tr[k]]
            if len(members) < min_secs:  # < ~40 s of presence: noise / passers-by
                continue
            cen = E[members].mean(0); cen /= np.linalg.norm(cen)
            name, best = None, 0.0
            for nm, kv in known.items():
                s = float(np.dot(cen, np.array(kv["emb"])))
                if s > best:
                    name, best = (nm if s > 0.8 else None), s
            players.append({"team": team, "secs": len(members), "members": members, "name": name, "match": round(best, 3),
                            "centroid": cen.tolist(), "tracks": sorted({f"{dets[i]['setup']}:{dets[i]['tid']}" for i in members})})
    players.sort(key=lambda p: (p["team"], -p["secs"]))
    for n, p in enumerate(players, 1):
        p["id"] = n
    # contact sheet: 6 biggest crops per player
    font = ImageFont.truetype("arialbd.ttf", 28)
    TW, TH = 150, 260
    sheet = Image.new("RGB", (TW * 7, TH * len(players)), (24, 24, 24))
    for r, p in enumerate(players):
        best = sorted(p["members"], key=lambda i: -(dets[i]["box"][3] - dets[i]["box"][1]))
        picks = best[:: max(1, len(best) // 6)][:6]
        d = ImageDraw.Draw(sheet)
        d.rectangle([0, r * TH, TW, (r + 1) * TH], fill=(255, 106, 19) if p["team"] == "orange" else (170, 210, 40))
        d.text((12, r * TH + 20), f"#{p['id']}", font=font, fill="black")
        d.text((12, r * TH + 60), p["name"] or "?", font=ImageFont.truetype("arial.ttf", 20), fill="black")
        d.text((12, r * TH + 90), f"{p['secs'] // 60}m on cam", font=ImageFont.truetype("arial.ttf", 18), fill="black")
        for j, i in enumerate(picks):
            im = Image.open(os.path.join(bbconfig.F5, f"{dets[i]['k']:05d}.jpg")).convert("RGB")
            c = crop(im, dets[i]["box"], 0.2)
            c.thumbnail((TW - 6, TH - 6))
            sheet.paste(c, (TW * (j + 1) + 3, r * TH + 3))
        p["photo_det"] = picks[0]
    out = os.path.join(bbconfig.WORK, "players_sheet.jpg")
    sheet.save(out, quality=88)
    json.dump([{k: v for k, v in p.items() if k != "members"} | {"n_members": len(p["members"])} for p in players],
              open(bbconfig.data("players_auto.json"), "w"), indent=1)
    json.dump({p["id"]: p["members"] for p in players}, open(bbconfig.data("players_members.json"), "w"))
    print(len(players), "players ->", out)


def name(mapping):
    """mapping: {"<id>": "<name>"} ; saves data/players.json and adds/updates known.json."""
    m = json.loads(mapping)
    auto = json.load(open(bbconfig.data("players_auto.json")))
    dets = json.load(open(bbconfig.data("people_dets.json")))
    known = json.load(open(KNOWN)) if os.path.exists(KNOWN) else {}
    os.makedirs(os.path.join(bbconfig.PIPELINE, "players"), exist_ok=True)
    out = []
    for p in auto:
        nm = m.get(str(p["id"])) or p["name"]
        if not nm:
            continue
        d = dets[p["photo_det"]]
        photo = bbconfig.data(f"photo_{nm}.png")
        im = Image.open(os.path.join(bbconfig.F5, f"{d['k']:05d}.jpg")).convert("RGB")
        c = crop(im, d["box"], 0.25)
        c.resize((450, int(450 * c.height / c.width)), Image.LANCZOS).save(photo)
        out.append({"id": p["id"], "name": nm, "team": p["team"], "photo": photo, "tracks": p["tracks"]})
        k = known.get(nm, {"emb": p["centroid"], "games": 0})
        e = (np.array(k["emb"]) * k["games"] + np.array(p["centroid"])) / (k["games"] + 1)
        known[nm] = {"emb": (e / np.linalg.norm(e)).tolist(), "games": k["games"] + 1}
    json.dump(out, open(bbconfig.data("players.json"), "w"), indent=1)
    json.dump(known, open(KNOWN, "w"))
    print("named", len(out), "| known players:", sorted(known))


def ask(max_tiles=40, min_secs=8, dist=0.05):
    """Numbered naming sheet: one tile per tracker segment group (pure: one tracked person), 3 crops per tile.
    Writes WORK/naming_sheet_<n>.jpg (+ data/naming_tiles.json). Barak replies 'tile -> name'."""
    from sklearn.cluster import AgglomerativeClustering
    dets = json.load(open(bbconfig.data("people_dets.json")))
    E = np.load(bbconfig.data("people_emb.npz"))["emb"]
    tiles = []
    # a tracker segment gets ONE team: the colour seen on most of its crops (a pinnie flickers in and out of the torso box)
    alltr = collections.defaultdict(list)
    for i, d in enumerate(dets):
        if d["tid"] >= 0:
            alltr[(d["setup"], d["tid"])].append(i)
    major = {k: collections.Counter(dets[i]["team"] for i in v).most_common(1)[0][0] for k, v in alltr.items()}
    for team in ("orange", "lime", "plain"):
        tr = {k: v for k, v in alltr.items() if major[k] == team}
        keys = [k for k, v in tr.items() if len(v) >= min_secs]
        if not keys:
            continue
        M = np.stack([E[tr[k]].mean(0) for k in keys]); M /= np.linalg.norm(M, axis=1, keepdims=True)
        lab = AgglomerativeClustering(n_clusters=None, distance_threshold=dist, metric="cosine",
                                      linkage="complete").fit_predict(M) if len(keys) > 1 else [0]
        for c in sorted(set(lab)):
            ks = [k for k, l in zip(keys, lab) if l == c]
            mem = [i for k in ks for i in tr[k]]
            tiles.append({"team": team, "tracks": [f"{a}:{b}" for a, b in ks], "members": mem, "secs": len(mem)})
    tiles.sort(key=lambda t: -t["secs"])
    dropped = tiles[max_tiles:]
    tiles = sorted(tiles[:max_tiles], key=lambda t: (t["team"], -t["secs"]))
    font = ImageFont.truetype("arialbd.ttf", 30)
    TW, TH, per = 360, 330, 12
    for s in range(0, len(tiles), per):
        chunk = tiles[s:s + per]
        sheet = Image.new("RGB", (TW * 4, TH * ((len(chunk) + 3) // 4)), (24, 24, 24))
        for j, t in enumerate(chunk):
            n = s + j + 1
            t["n"] = n
            best = sorted(t["members"], key=lambda i: -(dets[i]["box"][3] - dets[i]["box"][1]))
            picks = [best[0], best[len(best) // 3], best[2 * len(best) // 3]]
            x0, y0 = (j % 4) * TW, (j // 4) * TH
            for q, i in enumerate(picks):
                im = Image.open(os.path.join(bbconfig.F5, f"{dets[i]['k']:05d}.jpg")).convert("RGB")
                c = crop(im, dets[i]["box"], 0.2)
                sc = min(112 / c.width, 280 / c.height)
                c = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS)
                sheet.paste(c, (x0 + 4 + q * 118, y0 + 44))
            d = ImageDraw.Draw(sheet)
            col = {"orange": (255, 106, 19), "lime": (170, 210, 40)}.get(t["team"], (200, 200, 200))
            d.rectangle([x0 + 2, y0 + 2, x0 + 88, y0 + 38], fill=col)
            d.text((x0 + 10, y0 + 4), f"{n}", font=font, fill="black")
        sheet.save(os.path.join(bbconfig.WORK, f"naming_sheet_{s // per + 1}.jpg"), quality=88)
    json.dump([{k: v for k, v in t.items()} for t in tiles], open(bbconfig.data("naming_tiles.json"), "w"))
    print(len(tiles), "tiles;", len(dropped), "short groups not shown", sum(t["secs"] for t in dropped), "s")


def learn(mapping):
    """mapping: {"<tile n>": "<name>"} -> train a player classifier from the named tiles, label every detection,
    store per-player training sets in PIPELINE/players/<name>_train.npz for future games."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    m = {int(k): v.strip() for k, v in json.loads(mapping).items() if v and v.strip()}
    tiles = json.load(open(bbconfig.data("naming_tiles.json")))
    dets = json.load(open(bbconfig.data("people_dets.json")))
    E = np.load(bbconfig.data("people_emb.npz"))["emb"]
    X, y = [], []
    for t in tiles:
        if t["n"] in m:
            X.append(E[t["members"]]); y += [m[t["n"]]] * len(t["members"])
    X = np.vstack(X)
    store = os.path.join(bbconfig.PIPELINE, "players")
    os.makedirs(store, exist_ok=True)
    for nm in sorted(set(y)):  # add earlier games' crops of the same players
        p = os.path.join(store, f"{nm}_train.npz")
        if os.path.exists(p):
            old = np.load(p)["X"]; X = np.vstack([X, old]); y += [nm] * len(old)
    for nm in sorted(set(y)):
        np.savez_compressed(os.path.join(store, f"{nm}_train.npz"), X=X[np.array(y) == nm].astype(np.float32))
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced"))
    clf.fit(X, y)
    prob = clf.predict_proba(E)
    names = list(clf.classes_)
    # smooth over tracker segments
    tr = collections.defaultdict(list)
    for i, d in enumerate(dets):
        tr[(d["setup"], d["tid"])].append(i)
    who = [None] * len(dets)
    for k, ids in tr.items():
        pm = prob[ids].mean(0)
        best = int(pm.argmax())
        if pm[best] >= 0.6 and k[1] >= 0:
            for i in ids:
                who[i] = names[best]
    json.dump([{"t": d["t"], "box": d["box"], "team": d["team"], "name": w} for d, w in zip(dets, who)],
              open(bbconfig.data("players_timeline.json"), "w"))
    cnt = collections.Counter(w for w in who if w)
    print("players:", {n: f"{c // 60}m{c % 60:02d}s on camera" for n, c in cnt.most_common()})


if __name__ == "__main__":
    if sys.argv[1] == "ask":
        ask(); sys.exit()
    if sys.argv[1] == "learn":
        learn(sys.argv[2]); sys.exit()
    cmd = sys.argv[1]
    if cmd == "embed":
        embed()
    elif cmd == "cluster":
        cluster(*(float(x) for x in sys.argv[2:3]))
    else:
        name(sys.argv[2])

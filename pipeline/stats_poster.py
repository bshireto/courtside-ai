# -*- coding: utf-8 -*-
"""Vertical box-score image (1080 x 1920) for sharing on a phone.

  BB_GAME=<game> python stats_poster.py     -> <game>/output/Box_Score_Vertical.png  (+ WORK/statsimg/preview_400.png)

Reads data/stats.json (players + attempts) and data/players.json (photos, teams); every number on the image comes
from those files. Layout: kicker + date, title, four "leader" chips, one table (avatar, name, MIN, PTS, FG, FG%, 3PT,
AST - sorted by points, then assists, then name), team legend + totals, sign-off line.
Optional data/poster_photos.json picks a better avatar per player:
  {"Name": {"t": <second>, "idx": <person index, left to right, as in roster_frame.py>, "cx": 0.5, "dy": 0.0, "zoom": 0.88}}
(cx = where the head is across the crop, dy shifts the circle down; without "t" the players.json photo is used).
Faces in a wide night video are ~20 px, so the circle shows head AND torso: a tighter crop only gets blurrier.
The design won a three-way comparison (table vs cards vs poster) on phone legibility; the leader chips come from the poster.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

STATS_JSON = bbconfig.data("stats.json")
PLAYERS_JSON = bbconfig.data("players.json")
PHOTOS_JSON = bbconfig.data("poster_photos.json")
STILL_PNG = os.path.join(bbconfig.WORK, "render", "recap", "still.png")
OUT_PNG = os.path.join(bbconfig.GAME_DIR, "output", "Box_Score_Vertical.png")
OUT_PHONE = os.path.join(bbconfig.WORK, "statsimg", "preview_400.png")
FONT_DIR = r"C:\Windows\Fonts"

TITLE = bbconfig.CFG.get("title", "PICKUP RUN")
DATE = bbconfig.CFG.get("date", "")
KICKER = "BOX SCORE"
SIGN_OFF = "EVERY BASKET CHECKED FRAME BY FRAME"
MIN_FGA = 8                 # attempts needed to qualify for the FG% lead
USER_NAME = (bbconfig.CFG.get("user") or {}).get("name", "")
BLUR_OTHERS = os.environ.get("BB_BLUR_OTHERS", "") == "1"   # blur every photo except the user's (for public copies)

# ----------------------------------------------------------------------------
# canvas + palette
# ----------------------------------------------------------------------------
W, H = 1080, 1920
SS = 2                      # supersampling factor (shapes are drawn 2x, then downscaled)
M = 56                      # safe margin on every side
X0, X1 = M, W - M           # content edges

BG = (8, 11, 17)
ROW_A = (21, 27, 38)        # zebra, lighter
ROW_B = (15, 20, 29)        # zebra, darker
HEAD_BG = (30, 40, 58)      # table header strip
CHIP_BG = (24, 31, 45)
INK = (246, 248, 251)       # primary text
INK_2 = (222, 228, 238)     # regular numbers
INK_3 = (160, 172, 192)     # secondary numbers / labels
INK_4 = (140, 152, 172)     # zeros
INK_5 = (104, 116, 136)     # slashes, dividers
ACCENT = (120, 208, 255)    # column leaders (never a team colour)
TEAM = {"orange": (255, 106, 19), "lime": (170, 210, 40)}
TEAM_LABEL = {"orange": "ORANGE PINNIES", "lime": "LIME PINNIES"}

# ----------------------------------------------------------------------------
# layout (final-image pixels)
# ----------------------------------------------------------------------------
KICK_TOP = M
TITLE_TOP = 130             # top of the title capitals
CHIP_GAP_TOP = 38           # title bottom -> leader chips
CHIP_H = 100
CHIP_GAP = 14
TABLE_GAP_TOP = 24          # chips -> table
HEAD_H = 70

NAME_SIZE = 58
NUM_SIZE = 58
PTS_SIZE = 94
HEAD_SIZE = 43
FOOT_SIZE = 36

BAR_W = 10                  # team colour bar on the row's left edge
AVATAR_D = 96
RING_GAP, RING_W = 3, 4
RIGHT_INSET = 22

_font_cache = {}


def bahn(size, variant="Bold Condensed"):
    """Bahnschrift variable font at `size` final-image px."""
    key = (size, variant)
    if key not in _font_cache:
        f = ImageFont.truetype(os.path.join(FONT_DIR, "bahnschrift.ttf"), int(round(size * SS)))
        f.set_variation_by_name(variant.encode("ascii"))
        _font_cache[key] = f
    return _font_cache[key]


def tw(s, font, track=0.0):
    """Text advance width in final px."""
    return (font.getlength(s) + track * SS * max(len(s) - 1, 0)) / SS


def glyph_h(font, sample="0"):
    """Height above the baseline of `sample` in final px."""
    return -font.getbbox(sample, anchor="ls")[1] / SS


def ink(font, s):
    """Ink box of `s` in supersampled px relative to a left/baseline origin (side bearings removed)."""
    asc, desc = font.getmetrics()
    pad = 24
    im = Image.new("L", (int(font.getlength(s)) + 2 * pad + 8, asc + desc + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad, pad + asc), s, font=font, fill=255, anchor="ls")
    b = im.point(lambda v: 255 if v > 96 else 0).getbbox()
    return (b[0] - pad, b[1] - pad - asc, b[2] - pad, b[3] - pad - asc)


def bearings(font, s):
    b = ink(font, s)
    return b[0] / float(SS), (font.getlength(s) - b[2]) / float(SS)


class Canvas:
    def __init__(self, w, h, bg):
        self.im = Image.new("RGB", (w * SS, h * SS), bg)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def rect(self, x0, y0, x1, y1, fill=None, r=0, outline=None, width=0):
        box = [x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1]
        if r:
            self.d.rounded_rectangle(box, radius=r * SS, fill=fill, outline=outline, width=int(width * SS))
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=int(width * SS))

    def ellipse(self, cx, cy, rad, fill=None, outline=None, width=0):
        box = [(cx - rad) * SS, (cy - rad) * SS, (cx + rad) * SS - 1, (cy + rad) * SS - 1]
        self.d.ellipse(box, fill=fill, outline=outline, width=int(width * SS))

    def line(self, x0, y0, x1, y1, fill, width=1):
        self.d.line([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, width=int(width * SS))

    def text(self, x, y, s, font, fill, anchor="ls", track=0.0):
        """anchor like PIL ('ls' = left/baseline, 'rs', 'ms'); `track` = letter spacing in px."""
        if not track:
            self.d.text((x * SS, y * SS), s, font=font, fill=fill, anchor=anchor)
            return
        w = tw(s, font, track)
        if anchor[0] == "r":
            x -= w
        elif anchor[0] == "m":
            x -= w / 2
        for ch in s:
            self.d.text((x * SS, y * SS), ch, font=font, fill=fill, anchor="l" + anchor[1])
            x += font.getlength(ch) / SS + track

    def paste(self, img, x, y, mask=None):
        self.im.paste(img, (int(round(x * SS)), int(round(y * SS))), mask)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def final(self):
        return self.im.resize((self.im.width // SS, self.im.height // SS), Image.LANCZOS)


def pct(made, att):
    return None if not att else made / att


def pct_str(made, att):
    p = pct(made, att)
    return "-" if p is None else "%d%%" % int(p * 100 + 0.5)


def leaders(players, value, qualify=lambda p: True, max_share=2):
    """Names holding the best value. Empty when the lead is zero or shared by more than `max_share`."""
    vals = {n: value(p) for n, p in players.items() if qualify(p) and value(p) is not None}
    if not vals:
        return []
    best = max(vals.values())
    if best <= 0:
        return []
    top = sorted(n for n, v in vals.items() if abs(v - best) < 1e-9)
    return top if len(top) <= max_share else []


# ----------------------------------------------------------------------------
# photos
# ----------------------------------------------------------------------------
_tracks = None


def person_crop(t, idx):
    """Padded crop of the idx-th tracked person (left to right) at second t, from the 5 fps frame dump."""
    global _tracks
    if _tracks is None:
        _tracks = {}
        for line in open(bbconfig.data("tracks.jsonl")):
            r = json.loads(line)
            _tracks[r["k"]] = r
    k = int(round(t * 5)) + 1
    ps = sorted([p for p in _tracks[k]["p"] if p[5] - p[3] >= 80 and p[1] >= 0.35], key=lambda p: p[2])
    x0, y0, x1, y1 = ps[idx][2:6]
    w, h = x1 - x0, y1 - y0
    fp = os.path.join(bbconfig.F5, "%05d.jpg" % k)
    if os.path.exists(fp):
        im = Image.open(fp).convert("RGB")
    else:                                   # the 5 fps dump is temporary: grab the frame from the video instead
        import subprocess, io
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % ((k - 1) / 5.0), "-i", bbconfig.CFG["video"], "-frames:v", "1",
                              "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "2", "-"], capture_output=True, check=True).stdout
        im = Image.open(io.BytesIO(raw)).convert("RGB")
    return im.crop((int(x0 - w * 0.30), int(y0 - h * 0.10), int(x1 + w * 0.30), int(y1 + h * 0.05)))


def avatar(im, diameter, cx=0.5, dy=0.0, zoom=0.88):
    """Head-and-torso circle from a full-body crop: top 45%, squared, slightly tightened.
    cx = where the head is across the crop (0..1); dy shifts down as a fraction of the circle."""
    w, h = im.size
    side = min(w, int(h * 0.45))
    s = int(side * zoom)
    x0 = int(cx * w - s / 2.0)
    y0 = int(side * 0.03 + dy * s)
    x0 = max(0, min(w - s, x0)); y0 = max(0, min(h - s, y0))
    im = im.crop((x0, y0, x0 + s, y0 + s)).resize((diameter * SS, diameter * SS), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.6 * SS, percent=80, threshold=2))
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Brightness(im).enhance(1.08)
    big = Image.new("L", (diameter * SS * 2, diameter * SS * 2), 0)
    ImageDraw.Draw(big).ellipse([0, 0, big.width - 1, big.height - 1], fill=255)
    return im, big.resize((diameter * SS, diameter * SS), Image.LANCZOS)


def hero(canvas, height):
    """Darkened court still across the top, fading into the background."""
    if not os.path.exists(STILL_PNG):
        return
    still = Image.open(STILL_PNG).convert("RGB")
    sw, sh = still.size
    cw = int(sw * 0.755)
    ch = int(cw * height / W)
    cx0 = sw - cw
    cy0 = max(0, min(sh - ch, int(sh * 0.16)))
    crop = still.crop((cx0, cy0, cx0 + cw, cy0 + ch)).resize((W * SS, height * SS), Image.LANCZOS)
    crop = crop.filter(ImageFilter.GaussianBlur(1.4 * SS))
    crop = ImageEnhance.Color(crop).enhance(0.8)
    crop = ImageEnhance.Brightness(crop).enhance(0.62)
    crop = Image.blend(crop, Image.new("RGB", crop.size, BG), 0.12)
    mask = Image.new("L", (1, height * SS), 0)
    px = mask.load()
    for y in range(height * SS):
        t = y / float(height * SS - 1)
        a = 1.0 if t < 0.42 else max(0.0, 1.0 - (t - 0.42) / 0.58)
        px[0, y] = int(255 * (a ** 1.3))
    canvas.paste(crop, 0, 0, mask.resize((W * SS, height * SS)))


# ----------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------
def load():
    stats = json.load(open(STATS_JSON, encoding="utf-8"))
    roster = json.load(open(PLAYERS_JSON, encoding="utf-8"))
    players, attempts = stats["players"], stats["attempts"]
    photos = {p["name"]: {"photo": p.get("photo")} for p in roster}
    if os.path.exists(PHOTOS_JSON):
        for n, v in json.load(open(PHOTOS_JSON, encoding="utf-8")).items():
            photos.setdefault(n, {}).update(v)
    order = sorted(players, key=lambda n: (-players[n]["points"], -players[n]["ast"], n))
    baskets = sum(1 for a in attempts if a.get("made"))
    shots = len(attempts)
    games = len({g for p in players.values() for g in p["games"]})
    assert sum(p["fgm"] for p in players.values()) == baskets, "player makes do not add up to the attempts list"
    assert sum(p["fga"] for p in players.values()) == shots, "player attempts do not add up to the attempts list"
    return players, photos, order, baskets, shots, games


# ----------------------------------------------------------------------------
# render
# ----------------------------------------------------------------------------
def render():
    players, photos, order, baskets, shots, games = load()
    n = len(order)
    c = Canvas(W, H, BG)

    f_name = bahn(NAME_SIZE)
    f_num = bahn(NUM_SIZE)
    f_pts = bahn(PTS_SIZE)
    f_head = bahn(HEAD_SIZE)

    def minutes(p):
        return int(p["minutes"] + 0.5)

    lead_defs = [
        ("pts", "TOP SCORER", leaders(players, lambda p: p["points"]), lambda p: str(p["points"])),
        ("fgp", "BEST FG%", leaders(players, lambda p: pct(p["fgm"], p["fga"]), qualify=lambda p: p["fga"] >= MIN_FGA),
         lambda p: pct_str(p["fgm"], p["fga"])),
        ("tp", "MOST THREES", leaders(players, lambda p: p["tpm"]), lambda p: str(p["tpm"])),
        ("ast", "MOST ASSISTS", leaders(players, lambda p: p["ast"]), lambda p: str(p["ast"])),
    ]
    lead = {k: set(names) for k, _, names, _ in lead_defs}

    # ---------------- title band ----------------
    probe = bahn(120, "Bold SemiCondensed")
    pb = ink(probe, TITLE)
    t_size = 120 * (X1 - X0) * SS / float(pb[2] - pb[0])
    f_title = bahn(t_size, "Bold SemiCondensed")
    tb = ink(f_title, TITLE)
    title_h = -tb[1] / float(SS)
    t_base = TITLE_TOP + title_h
    chips_top = t_base + CHIP_GAP_TOP
    table_top = int(chips_top + CHIP_H + TABLE_GAP_TOP)
    hero(c, int(chips_top + 60))

    # kicker tab (left) + date (right) joined by a hairline
    f_date = bahn(54, "Bold SemiCondensed")
    date_h = -ink(f_date, DATE or "0")[1] / float(SS)
    kick_h = int(round(date_h)) + 4
    f_kick = bahn(32, "Bold SemiCondensed")
    kick_w = tw(KICKER, f_kick, 3) + 36
    c.rect(X0, KICK_TOP, X0 + kick_w, KICK_TOP + kick_h, fill=INK, r=4)
    c.text(X0 + kick_w / 2, KICK_TOP + kick_h / 2 + glyph_h(f_kick, "H") / 2, KICKER, f_kick, BG, "ms", track=3)
    if DATE:
        c.text(X1 + bearings(f_date, DATE)[1], KICK_TOP + 2 + date_h, DATE, f_date, INK, "rs")
        c.line(X0 + kick_w + 22, KICK_TOP + kick_h / 2, X1 - tw(DATE, f_date) - 20, KICK_TOP + kick_h / 2, (255, 255, 255, 80), 2)

    # title fitted to the content width, with a soft shadow so it separates from the photo
    sh = Image.new("L", c.im.size, 0)
    ImageDraw.Draw(sh).text(((X0 * SS) - tb[0], (t_base + 6) * SS), TITLE, font=f_title, fill=165, anchor="ls")
    sh = sh.filter(ImageFilter.GaussianBlur(11 * SS))
    c.paste(Image.new("RGB", c.im.size, (0, 0, 0)), 0, 0, sh)
    c.d.text(((X0 * SS) - tb[0], t_base * SS), TITLE, font=f_title, fill=INK, anchor="ls")

    # ---------------- leader chips ----------------
    chips = [(lab, names, fmt) for _, lab, names, fmt in lead_defs if names]
    if chips:
        cw_ = (X1 - X0 - CHIP_GAP * (len(chips) - 1)) / float(len(chips))
        f_cl = bahn(27, "SemiBold Condensed")
        pad = 16
        for i, (lab, names, fmt) in enumerate(chips):
            cx0 = X0 + i * (cw_ + CHIP_GAP)
            c.rect(cx0, chips_top, cx0 + cw_, chips_top + CHIP_H, fill=CHIP_BG + (235,), r=14)
            c.text(cx0 + pad, chips_top + 16 + glyph_h(f_cl, "H"), lab, f_cl, ACCENT, "ls", track=1.5)
            who = " / ".join(x.upper() for x in names)
            val = fmt(players[names[0]])
            size = 50
            while True:                                  # largest size at which name + number fit the chip
                f_cv = bahn(size)
                if tw(who, f_cv, 0.5) + 14 + tw(val, f_cv) <= cw_ - 2 * pad or size <= 30:
                    break
                size -= 1
            base = chips_top + CHIP_H - 17
            c.text(cx0 + pad, base, who, f_cv, INK, "ls", track=0.5)
            c.text(cx0 + cw_ - pad + bearings(f_cv, val[-1])[1], base, val, f_cv, ACCENT, "rs")

    # ---------------- bottom block geometry ----------------
    f_foot = bahn(FOOT_SIZE, "SemiBold Condensed")
    f_foot_b = bahn(FOOT_SIZE)
    foot_cap = glyph_h(f_foot_b, "H")
    line_b = H - M - 2                        # sign-off baseline
    line_a = line_b - foot_cap - 26           # legend + totals baseline
    table_bottom_max = line_a - foot_cap - 30

    row_h = int((table_bottom_max - table_top - HEAD_H) // max(n, 1))
    rows_top = table_top + HEAD_H
    table_bottom = rows_top + row_h * n

    ring_r = AVATAR_D / 2 + RING_GAP + RING_W
    av_cx = X0 + BAR_W + 14 + ring_r
    name_x = av_cx + ring_r + 16
    name_track = 0.5
    name_w = max(tw(nm.upper(), f_name, name_track) for nm in order)

    cols = [
        # gw = weight of the gap in front of the column (FG% hugs the FG it is derived from)
        dict(key="min", head="MIN", kind="num", font=f_num, color=INK_3, gw=1.0, val=lambda p: str(minutes(p))),
        dict(key="pts", head="PTS", kind="ctr", font=f_pts, color=INK, gw=1.0, val=lambda p: str(p["points"])),
        dict(key="fg", head="FG", kind="frac", font=f_num, color=INK_2, gw=1.15, val=lambda p: (p["fgm"], p["fga"])),
        dict(key="fgp", head="FG%", kind="num", font=f_num, color=INK_3, gw=0.75, val=lambda p: pct_str(p["fgm"], p["fga"])),
        dict(key="tp", head="3PT", kind="frac", font=f_num, color=INK_2, gw=1.05, val=lambda p: (p["tpm"], p["tpa"])),
        dict(key="ast", head="AST", kind="num", font=f_num, color=INK_2, gw=0.95, val=lambda p: str(p["ast"])),
    ]
    slash_pad = 3
    for col in cols:
        f = col["font"]
        if col["kind"] == "frac":
            col["lw"] = max(tw(str(col["val"](players[nm])[0]), f) for nm in order)
            col["rw"] = max(tw(str(col["val"](players[nm])[1]), f) for nm in order)
            col["sw"] = tw("/", f) + 2 * slash_pad
            col["cw"] = col["lw"] + col["sw"] + col["rw"]
        else:
            col["cw"] = max(tw(col["val"](players[nm]), f) for nm in order)
        col["w"] = max(col["cw"], tw(col["head"], f_head, 1.5))

    stats_left = name_x + name_w
    stats_right = X1 - RIGHT_INSET
    gap = (stats_right - stats_left - sum(col["w"] for col in cols)) / sum(col["gw"] for col in cols)
    x = stats_left
    for col in cols:
        x += gap * col["gw"]
        col["x0"], col["x1"] = x, x + col["w"]
        col["cx"] = x + col["w"] / 2
        col["c0"] = col["cx"] - col["cw"] / 2
        col["c1"] = col["cx"] + col["cw"] / 2
        x += col["w"]
    print("title cap %.0f px | chips %.0f | table %d..%d | row_h=%d | column gap=%.1f" % (
        title_h, chips_top, table_top, table_bottom, row_h, gap))
    print("glyph heights px: name=%.0f num=%.0f pts=%.0f header=%.0f footer=%.0f" % (
        glyph_h(f_name, "H"), glyph_h(f_num), glyph_h(f_pts), glyph_h(f_head, "H"), foot_cap))
    assert gap >= 20, "stat columns are too tight (%.1f px)" % gap

    # ---------------- table surface (rounded as one block) ----------------
    tbl = Image.new("RGB", ((X1 - X0) * SS, (table_bottom - table_top) * SS), ROW_B)
    td = ImageDraw.Draw(tbl, "RGBA")
    td.rectangle([0, 0, tbl.width, HEAD_H * SS - 1], fill=HEAD_BG)
    for i, nm in enumerate(order):
        y0 = (HEAD_H + i * row_h) * SS
        td.rectangle([0, y0, tbl.width, y0 + row_h * SS - 1], fill=ROW_A if i % 2 == 0 else ROW_B)
        td.rectangle([0, y0 + 2 * SS, BAR_W * SS - 1, y0 + (row_h - 2) * SS - 1], fill=TEAM[players[nm]["team"]])
    pc = next(col for col in cols if col["key"] == "pts")
    band_pad = min(gap / 2, 18)
    td.rectangle([(pc["x0"] - band_pad - X0) * SS, 0, (pc["x1"] + band_pad - X0) * SS - 1, tbl.height], fill=(255, 255, 255, 16))
    tmask = Image.new("L", tbl.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle([0, 0, tbl.width - 1, tbl.height - 1], radius=22 * SS, fill=255)
    c.paste(tbl, X0, table_top, tmask)

    # ---------------- header row ----------------
    hb = table_top + HEAD_H / 2 + glyph_h(f_head, "H") / 2
    c.text(name_x, hb, "PLAYER", f_head, INK_3, "ls", track=1.5)
    for col in cols:
        c.text(col["cx"], hb, col["head"], f_head, INK if col["key"] == "pts" else INK_3, "ms", track=1.5)

    # ---------------- player rows ----------------
    for i, nm in enumerate(order):
        p = players[nm]
        cy = rows_top + i * row_h + row_h / 2.0
        team_rgb = TEAM[p["team"]]

        c.ellipse(av_cx, cy, ring_r, outline=team_rgb, width=RING_W)
        ph = photos.get(nm, {})
        src = None
        if "t" in ph:
            src = person_crop(ph["t"], ph["idx"])
        elif ph.get("photo") and os.path.exists(ph["photo"]):
            src = Image.open(ph["photo"]).convert("RGB")
        if src is not None:
            av, am = avatar(src, AVATAR_D, ph.get("cx", 0.5), ph.get("dy", 0.0), ph.get("zoom", 0.88))
            if BLUR_OTHERS and nm != USER_NAME:       # public copies: only the user's own face stays sharp
                av = av.filter(ImageFilter.GaussianBlur(max(6, AVATAR_D // 9)))
            c.paste(av, av_cx - AVATAR_D / 2, cy - AVATAR_D / 2, am)
        else:
            c.ellipse(av_cx, cy, AVATAR_D / 2, fill=(40, 48, 62))

        c.text(name_x, cy + glyph_h(f_name, "H") / 2, nm.upper(), f_name, INK, "ls", track=name_track)

        for col in cols:
            f = col["font"]
            base = cy + glyph_h(f, "0") / 2
            v = col["val"](p)
            is_lead = nm in lead.get(col["key"], ())
            if col["kind"] == "frac":
                made, att = v
                slash_cx = col["c0"] + col["lw"] + col["sw"] / 2
                colr = ACCENT if is_lead else (INK_4 if att == 0 else col["color"])
                c.text(slash_cx - col["sw"] / 2, base, str(made), f, colr, "rs")
                c.text(slash_cx, base, "/", f, INK_5, "ms")
                c.text(slash_cx + col["sw"] / 2, base, str(att), f, colr, "ls")
            else:
                colr = ACCENT if is_lead else (INK_4 if v in ("0", "-") else col["color"])
                if col["kind"] == "ctr":
                    c.text(col["cx"], base, v, f, colr, "ms")
                else:
                    c.text(col["c1"], base, v, f, colr, "rs")

    # ---------------- legend + totals (line A) ----------------
    x = X0
    for team in ("orange", "lime"):
        if not any(p["team"] == team for p in players.values()):
            continue
        c.rect(x, line_a - foot_cap + 1, x + 24, line_a - 1, fill=TEAM[team], r=5)
        c.text(x + 36, line_a, TEAM_LABEL[team], f_foot, INK_2, "ls", track=0.8)
        x += 36 + tw(TEAM_LABEL[team], f_foot, 0.8) + 34
    legend_right = x - 34
    totals = [(str(baskets), "BASKETS"), (str(shots), "SHOTS"), (str(games), "GAMES")]
    sep = 15
    widths = [tw(num, f_foot_b) + 9 + tw(lab, f_foot, 0.6) for num, lab in totals]
    total_w = sum(widths) + 2 * sep * (len(totals) - 1)
    assert X1 - total_w - legend_right >= 28, "legend and totals collide on the bottom line"
    x = X1 - total_w
    for k, (num, lab) in enumerate(totals):
        c.text(x, line_a, num, f_foot_b, INK, "ls")
        c.text(x + tw(num, f_foot_b) + 9, line_a, lab, f_foot, INK_3, "ls", track=0.6)
        x += widths[k]
        if k < len(totals) - 1:
            c.line(x + sep, line_a - foot_cap, x + sep, line_a, (255, 255, 255, 90), 2)
            x += 2 * sep

    # ---------------- sign-off (line B): centred between two hairlines ----------------
    sw_ = tw(SIGN_OFF, f_foot, 2.0)
    c.text(W / 2.0, line_b, SIGN_OFF, f_foot, INK_3, "ms", track=2.0)
    ymid = line_b - foot_cap / 2
    c.line(X0, ymid, W / 2.0 - sw_ / 2 - 22, ymid, (255, 255, 255, 60), 2)
    c.line(W / 2.0 + sw_ / 2 + 22, ymid, X1, ymid, (255, 255, 255, 60), 2)

    out = c.final()
    assert out.size == (W, H), out.size
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_PHONE), exist_ok=True)
    out.save(OUT_PNG)
    out.resize((400, int(round(400.0 * H / W))), Image.LANCZOS).save(OUT_PHONE)

    # what was drawn, for checking against stats.json
    print("%-9s %-6s %3s %3s %6s %4s %6s %3s" % ("name", "team", "MIN", "PTS", "FG", "FG%", "3PT", "AST"))
    for nm in order:
        p = players[nm]
        print("%-9s %-6s %3d %3d %6s %4s %6s %3d" % (
            nm, p["team"], minutes(p), p["points"], "%d/%d" % (p["fgm"], p["fga"]),
            pct_str(p["fgm"], p["fga"]), "%d/%d" % (p["tpm"], p["tpa"]), p["ast"]))
    print("leaders:", {lab: names for _, lab, names, _ in lead_defs})
    print("totals: %d baskets | %d shots | %d games" % (baskets, shots, games))
    print("saved", OUT_PNG)


if __name__ == "__main__":
    render()

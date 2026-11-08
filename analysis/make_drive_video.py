"""Render one coaching video from a list of segments. Second generation of make_coaching_clip.py, for the richer videos Barak asked
for on 2026-10-12: more than one slow motion, stops with lines drawn on them, a simulation, a closing sentence.

  python make_drive_video.py spec.json            # renders spec["out"] and a contact sheet next to it (<out>_sheet.jpg)

spec = {
  "reel": "<reel mp4>", "out": "<out.mp4>",
  "segments": [
    {"type": "live", "start": 168.4, "end": 172.8, "tag": "מהירות רגילה",
     "captions": [{"from": 0.0, "to": 2.2, "text": "..."}, ...]},                       # times are seconds from the segment start
    {"type": "slow", "start": 170.4, "end": 172.1, "speed": 0.5, "view": {"center": [640, 580], "crop_w": 1300},
     "tag": "הילוך איטי 1", "caption": "..."},                                         # speed: 0.5, 0.4, 0.333 or 0.25
    {"type": "freeze", "at": 171.4, "secs": 3.0, "view": {"center": [520, 590], "crop_w": 700}, "tag": "עצירה", "caption": "...",
     "draw": [{"at": 0.4, "rings": [{"at": [566, 553], "r": 16, "col": "red"}], "labels": [{"at": [585, 520], "text": "היד של המגן"}]},
              {"at": 1.3, "arrows": [{"pts": [[493, 620], [560, 640], [640, 636]], "col": "green"}],
               "zones": [{"poly": [[600, 640], [760, 650], [760, 610], [600, 610]], "col": "green"}]}]},
    {"type": "still", "image": "<jpg/png, 16:9>", "secs": 4.5, "tag": "סימולציה: ...", "caption": "..."},
    {"type": "card", "title": "משפט לעצמך", "text": "...", "foot": "קליפ 15 · 2:51", "secs": 2.8}
  ]
}
All coordinates are FULL-FRAME pixels of the 1920x1080 reel; the tool maps them into the view. "view" defaults to the whole frame.
"draw" is one layer (a dict) or a list of layers; each layer appears "at" seconds into the stop and stays. Colours: green (the better
path / free space), red (what went wrong), yellow (the ball / attention), blue (a teammate), white.
Radius "r" of a ring and label "size" are in full-frame pixels and output pixels respectively (label size default 40).

Read-then-watch pacing (2026-10-12, "I'm not able to both read and view"): text belongs on a frozen picture, motion plays clean.
    {"type": "stop", "at": 169.6, "view": {...}, "tag": "עצירה 1",
     "steps": [{"caption": "...", "draw": {<layer>}}, {"caption": "...", "draw": {<layer>}, "secs": 5.0}]}
  A stop is one frozen frame shown step by step: each step has its own caption and ADDS its layer to the ones before it.
  Put a stop at the "end" of a slow motion (and start the next slow motion at the same time) and the picture simply pauses.
  spec["pace"] = {"per_word": 0.38, "look": 1.4, "min": 3.0}: a step / freeze / still / card without "secs" lasts
  look + per_word * words (caption + the labels that step adds; a still may give "words" for the text inside the picture).
  spec["caption_size"] (default 46). A slow motion takes "flash": false when it continues after a stop.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
from bidi.algorithm import get_display
from captions import overlay_png, font, wrap

spec = json.load(open(sys.argv[1], encoding="utf-8"))
tmp = tempfile.mkdtemp(prefix="drivevid_")
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "60", "-pix_fmt", "yuv420p", "-video_track_timescale", "15360",
       "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
COL = {"green": (0, 160, 70), "red": (239, 59, 36), "yellow": (253, 187, 48), "blue": (0, 122, 193), "white": (255, 255, 255), "navy": (0, 45, 98)}
REEL = spec["reel"]
PACE = spec.get("pace")
CAP = int(spec.get("caption_size", 46))


def as_list(x):
    return [] if not x else ([x] if isinstance(x, dict) else list(x))


def nwords(*texts):
    return sum(len(t.split()) for t in texts if t)


def label_words(layers):
    return sum(len(lb["text"].split()) for ly in layers for lb in ly.get("labels", []))


def read_secs(n, default):
    """Seconds a text of n words stays on screen. Without spec["pace"] the old fixed default is used."""
    if not PACE:
        return default
    return round(max(PACE.get("min", 3.0), PACE.get("look", 1.4) + PACE.get("per_word", 0.38) * n), 2)


def expand_stops(segs):
    """A "stop" becomes one freeze per step; the layers of the earlier steps are the "base" of the later ones."""
    out = []
    for sg in segs:
        if sg["type"] != "stop":
            out.append(sg); continue
        prior, steps = [], sg["steps"]
        for k, st in enumerate(steps):
            new = [dict(ly, at=ly.get("at", 0.3)) for ly in as_list(st.get("draw"))]
            f = {"type": "freeze", "at": sg["at"], "view": sg.get("view"), "tag": st.get("tag", sg.get("tag", "עצירה")),
                 "caption": st.get("caption"), "base": list(prior), "draw": new, "step": f"{k + 1}/{len(steps)}"}
            if st.get("secs"):
                f["secs"] = st["secs"]
            if sg.get("fade_out") and k == len(steps) - 1:
                f["fade_out"] = True
            out.append(f); prior += new
    return out


def run(args, label):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"{label} failed:\n{r.stderr[-3000:]}")


def col(c, default="green"):
    c = c if c is not None else default
    return COL[c] if isinstance(c, str) else tuple(c)[:3]


def view_box(v):
    v = v or {}
    cw = int(max(480, min(1920, v.get("crop_w", 1920)))); cw -= cw % 2
    ch = int(round(cw * 9 / 16)); ch -= ch % 2
    cx, cy = v.get("center", [960, 540])
    x0 = int(max(0, min(1920 - cw, cx - cw / 2))); y0 = int(max(0, min(1080 - ch, cy - ch / 2)))
    return x0, y0, cw, ch


def draw_layer(layer, box, path):
    """One transparent 1920x1080 PNG with the zones, arrows, rings and labels of a layer, mapped from full-frame pixels into the view."""
    import math
    x0, y0, cw, ch = box
    s = 1920 / cw
    P = lambda p: ((p[0] - x0) * s, (p[1] - y0) * s)
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    zl = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); zd = ImageDraw.Draw(zl)
    for z in layer.get("zones", []):
        c = col(z.get("col"))
        zd.polygon([P(p) for p in z["poly"]], fill=c + (75,), outline=c + (230,))
    im = Image.alpha_composite(im, zl); d = ImageDraw.Draw(im)
    for a in layer.get("arrows", []):
        c = col(a.get("col")); pts = [P(p) for p in a["pts"]]; w = int(a.get("w", 10))
        (xa, ya), (xb, yb) = pts[-2], pts[-1]; ang = math.atan2(yb - ya, xb - xa); L = w * 3.6
        tip = (xb + L * 0.6 * math.cos(ang), yb + L * 0.6 * math.sin(ang))
        head = [tip, (xb + L * 0.75 * math.cos(ang + 2.45), yb + L * 0.75 * math.sin(ang + 2.45)), (xb + L * 0.75 * math.cos(ang - 2.45), yb + L * 0.75 * math.sin(ang - 2.45))]
        d.line(pts, fill=(0, 0, 0, 170), width=w + 6, joint="curve"); d.polygon(head, fill=(0, 0, 0, 170), outline=(0, 0, 0, 170), width=6)
        d.line(pts, fill=c + (255,), width=w, joint="curve"); d.polygon(head, fill=c + (255,))
    for r in layer.get("rings", []):
        c = col(r.get("col"), "red"); x, y = P(r["at"]); rad = r.get("r", 30) * s
        d.ellipse([x - rad, y - rad, x + rad, y + rad], outline=(0, 0, 0, 170), width=11)
        d.ellipse([x - rad, y - rad, x + rad, y + rad], outline=c + (255,), width=7)
    for lb in layer.get("labels", []):
        f = font(int(lb.get("size", 40))); vis = get_display(lb["text"]); tw = d.textlength(vis, font=f); th = int(lb.get("size", 40) * 1.3)
        x, y = P(lb["at"]); anchor = lb.get("anchor", "l")
        x = x - tw if anchor == "r" else (x - tw / 2 if anchor == "c" else x)
        x = max(24, min(1920 - tw - 24, x)); y = max(110, min(1080 - 250, y))
        c = col(lb.get("col"), "white")
        d.rectangle([x - 14, y - 8, x + tw + 14, y + th + 4], fill=(0, 0, 0, 175))
        if lb.get("col"):
            d.rectangle([x - 14, y - 8, x - 6, y + th + 4], fill=c + (255,))
        d.text((x, y), vis, fill="white", font=f)
    im.save(path)
    return path


def silence(secs):
    return ["-f", "lavfi", "-t", f"{secs:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]


def seg_live(i, sg):
    dur = sg["end"] - sg["start"]; n = int(round(dur * 30))
    x0, y0, cw, ch = view_box(sg.get("view"))
    inputs = ["-ss", f"{sg['start']:.3f}", "-t", f"{dur + 0.3:.3f}", "-i", REEL]
    chain = [f"[0:v]fps=30,trim=end_frame={n},setpts=N/30/TB,crop={cw}:{ch}:{x0}:{y0},scale=1920:1080:flags=lanczos[v0]"]
    last = "v0"; caps = sg.get("captions", [])
    if not caps and sg.get("tag"):
        caps = [{"from": 0, "to": dur, "text": None}]
    for k, c in enumerate(caps):
        png = overlay_png(os.path.join(tmp, f"s{i}_cap{k}.png"), caption=c.get("text"), tag=sg.get("tag", "מהירות רגילה"), caption_size=CAP)
        inputs += ["-i", png]
        chain.append(f"[{last}][{k + 1}:v]overlay=0:0:format=auto:enable='between(t,{c['from']},{c['to']})'[v{k + 1}]"); last = f"v{k + 1}"
    chain.append(f"[{last}]format=yuv420p[v]")
    af = f"[0:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample={n * 1600},asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st={dur - 0.05}:d=0.05[a]"
    out = os.path.join(tmp, f"s{i}.mov")
    run(inputs + ["-filter_complex", ";".join(chain) + ";" + af, "-map", "[v]", "-map", "[a]"] + ENC + [out], f"live {i}")
    return out, n / 30


def seg_slow(i, sg):
    s, e = sg["start"], sg["end"]; nin = int(round((e - s) * 30))
    fi = int(round(30 / sg.get("speed", 0.5))); nout = nin * fi // 30
    x0, y0, cw, ch = view_box(sg.get("view"))
    png = overlay_png(os.path.join(tmp, f"s{i}_cap.png"), caption=sg.get("caption"), tag=sg.get("tag", "הילוך איטי"), caption_size=CAP)
    flash = ",fade=t=in:st=0:d=0.2:color=white" if sg.get("flash", True) else ""
    pre = "scale=1280:720:flags=bicubic," if cw > 1100 else ""
    vf = (f"[0:v]fps=30,trim=end_frame={nin + 2},setpts=N/30/TB,crop={cw}:{ch}:{x0}:{y0},{pre}hqdn3d=1.5:1.5:6:6,"
          f"minterpolate=fps={fi}:mi_mode=mci,setpts={fi / 30}*PTS,fps=30,scale=1920:1080:flags=lanczos,"
          f"unsharp=5:5:0.6:5:5:0,trim=end_frame={nout},setpts=N/30/TB{flash}[base];"
          f"[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    out = os.path.join(tmp, f"s{i}.mov")
    run(["-ss", f"{s:.3f}", "-t", f"{e - s + 0.3:.3f}", "-i", REEL, "-i", png] + silence(nout / 30) +
        ["-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-shortest"] + ENC + [out], f"slow {i}")
    return out, nout / 30


def seg_freeze(i, sg):
    box = view_box(sg.get("view")); x0, y0, cw, ch = box
    layers, base = as_list(sg.get("draw")), as_list(sg.get("base"))
    secs = sg.get("secs") or read_secs(nwords(sg.get("caption")) + label_words(layers), 2.6); nf = int(round(secs * 30))
    cap = overlay_png(os.path.join(tmp, f"s{i}_cap.png"), caption=sg.get("caption"), tag=sg.get("tag", "עצירה"), caption_size=CAP)
    inputs = ["-ss", f"{sg['at']:.3f}", "-t", "0.2", "-i", REEL]
    chain = [f"[0:v]fps=30,trim=end_frame=1,setpts=N/30/TB,crop={cw}:{ch}:{x0}:{y0},scale=1920:1080:flags=lanczos,unsharp=5:5:0.6:5:5:0,"
             f"loop=loop={nf - 1}:size=1:start=0,setpts=N/30/TB[b0]"]
    last = "b0"; nin = 1
    if base:                                             # marks of the earlier steps: on screen from the first frame
        bim = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        for k, ly in enumerate(base):
            bim = Image.alpha_composite(bim, Image.open(draw_layer(ly, box, os.path.join(tmp, f"s{i}_base{k}.png"))))
        bpng = os.path.join(tmp, f"s{i}_base.png"); bim.save(bpng)
        inputs += ["-i", bpng]
        chain.append(f"[{last}][{nin}:v]overlay=0:0:format=auto[bb]"); last = "bb"; nin += 1
    for k, ly in enumerate(layers):
        png = draw_layer(ly, box, os.path.join(tmp, f"s{i}_ly{k}.png"))
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{secs:.3f}", "-i", png]
        chain.append(f"[{nin}:v]format=rgba,fade=t=in:st={float(ly.get('at', 0.35)):.2f}:d=0.25:alpha=1[l{k}]")
        chain.append(f"[{last}][l{k}]overlay=0:0:format=auto[b{k + 1}]"); last = f"b{k + 1}"; nin += 1
    ci = nin
    inputs += ["-i", cap] + silence(secs)
    tail = f",fade=t=out:st={secs - 0.35}:d=0.35" if sg.get("fade_out") else ""
    chain.append(f"[{last}][{ci}:v]overlay=0:0:format=auto,trim=end_frame={nf},setpts=N/30/TB{tail},format=yuv420p[v]")
    out = os.path.join(tmp, f"s{i}.mov")
    run(inputs + ["-filter_complex", ";".join(chain), "-map", "[v]", "-map", f"{ci + 1}:a", "-shortest"] + ENC + [out], f"freeze {i}")
    return out, nf / 30


def seg_image(i, img, secs, caption=None, tag=None):
    ipng = os.path.join(tmp, f"s{i}_img.png"); img.save(ipng)
    cpng = overlay_png(os.path.join(tmp, f"s{i}_cap.png"), caption=caption, tag=tag, caption_size=CAP)
    out = os.path.join(tmp, f"s{i}.mov"); nf = int(round(secs * 30))
    vf = (f"[0:v]fps=30,loop=loop={nf - 1}:size=1:start=0,setpts=N/30/TB[base];[base][1:v]overlay=0:0:format=auto,trim=end_frame={nf},setpts=N/30/TB,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={secs - 0.35}:d=0.35,format=yuv420p[v]")
    run(["-i", ipng, "-i", cpng] + silence(secs) + ["-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-shortest"] + ENC + [out], f"image {i}")
    return out, nf / 30


def seg_still(i, sg):
    img = Image.open(sg["image"]).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    secs = sg.get("secs") or read_secs(nwords(sg.get("caption"), sg.get("tag")) + int(sg.get("words", 0)), 4.5)
    return seg_image(i, img, secs, sg.get("caption"), sg.get("tag"))


def seg_card(i, sg):
    im = Image.new("RGB", (1920, 1080), COL["navy"]); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1920, 14], fill=COL["red"])
    ft = font(46); title = get_display(sg.get("title", "משפט לעצמך")); tw = d.textlength(title, font=ft)
    fb = font(int(sg.get("size", 80))); lines = wrap(sg["text"], fb, 1560); lh = int(sg.get("size", 80) * 1.3)
    y = 540 - (lh * len(lines)) / 2
    d.text(((1920 - tw) / 2, y - 110), title, fill=COL["yellow"], font=ft)
    for k, l in enumerate(lines):
        vis = get_display(l); lw = d.textlength(vis, font=fb)
        d.text(((1920 - lw) / 2, y + k * lh), vis, fill="white", font=fb)
    if sg.get("foot"):
        ff = font(36, bold=False); vis = get_display(sg["foot"]); fw = d.textlength(vis, font=ff)
        d.text(((1920 - fw) / 2, 1080 - 130), vis, fill=(201, 214, 229), font=ff)
    return seg_image(i, im, sg.get("secs") or read_secs(nwords(sg.get("text"), sg.get("title")), 2.8))


MAKE = {"live": seg_live, "slow": seg_slow, "freeze": seg_freeze, "still": seg_still, "card": seg_card}
parts, marks, timeline, t = [], [], [], 0.0
for i, sg in enumerate(expand_stops(spec["segments"])):
    out, dur = MAKE[sg["type"]](i, sg)
    parts.append(out)
    marks.append((sg["type"], t + (dur - 0.25 if sg["type"] == "freeze" else dur * 0.6)))
    timeline.append({"n": i, "type": sg["type"], "start": round(t, 2), "secs": round(dur, 2), "tag": sg.get("tag"), "step": sg.get("step"),
                     "text": sg.get("caption") or sg.get("text"), "reel": sg.get("at", sg.get("start"))})
    t += dur
lst = os.path.join(tmp, "list.txt")
open(lst, "w", encoding="utf-8").write("\n".join(f"file '{p.replace(chr(92), '/')}'" for p in parts))
run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", spec["out"]], "concat")

# contact sheet: one frame per segment (late in a stop, so every drawn layer is on)
tiles = []
for k, (typ, at) in enumerate(marks):
    fp = os.path.join(tmp, f"sheet{k}.jpg")
    run(["-ss", f"{max(0, at):.2f}", "-i", spec["out"], "-frames:v", "1", "-vf", "scale=960:540", fp], "sheet")
    tiles.append(Image.open(fp).convert("RGB"))
cols = 2 if len(tiles) <= 10 else 3; rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (960 * cols, 540 * rows), (20, 20, 20))
for k, im in enumerate(tiles):
    sheet.paste(im, ((k % cols) * 960, (k // cols) * 540))
sheet_path = os.path.splitext(spec["out"])[0] + "_sheet.jpg"
sheet.save(sheet_path, quality=82)
json.dump(timeline, open(os.path.splitext(spec["out"])[0] + "_timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", spec["out"], f"{t:.1f}s", "segments", len(parts), "| sheet", sheet_path)

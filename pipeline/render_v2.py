"""Render both deliverables to the research style guide (research_style_guide.md).

  python render_v2.py recap data/makes_final.json output/Every_Basket_Recap.mp4
  python render_v2.py reel  data/user_clips_final.json output/Barak_Offense_Reel.mp4

makes_final.json: [{"t_through", "t_release", "hoop", "team", "shot_type", "is_user",
                    "replay", "shooter_xy", "replay_pre"}]   (seconds)
user_clips_final.json: [{"start", "end"}]  (seconds)

Recap: title card 3 s -> every make in order (wide live clip T-5..T+1.5 with a basket
tally; eligible makes get one 0.5x motion-interpolated replay, reframed on shooter+rim
with an eased push-in) -> end card 5 s. Reel: plain hard cuts, no grade, no text.
Both: CRF 17 intermediates, concat with video copy, two-pass loudnorm to -14 LUFS,
plus a smaller share copy.
"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import bbconfig
SRC = bbconfig.VIDEO
WORK = _o.path.join(bbconfig.WORK, "render")
FONT_B = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_R = r"C:\Windows\Fonts\segoeui.ttf"
FF_FONT = "C\\:/Windows/Fonts/segoeuib.ttf"
RIM = bbconfig.RIM
DATE = bbconfig.CFG.get('date', '')
TITLE = bbconfig.CFG.get('title', 'PICKUP RUN')
GRADE = "curves=master='0/0 0.12/0.10 0.5/0.58 0.85/0.9 1/1',eq=saturation=1.25,unsharp=5:5:0.6:5:5:0"
NORM_V = "fps=30,trim=end_frame={n},setpts=N/30/TB,scale=1920:1080:in_range=full:out_range=tv:flags=lanczos,setsar=1"
NORM_A = "aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample={ns},asetpts=N/SR/TB"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-g", "60", "-pix_fmt", "yuv420p",
       "-profile:v", "high", "-level", "4.1", "-video_track_timescale", "15360", "-color_range", "tv",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
LEAD, TAIL = 5.0, 1.5
BOX = f"fontfile='{FF_FONT}':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=12|20"


def run(args, label):
    t = time.time()
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args, capture_output=True, text=True)
    if r.returncode:
        print(label, "FAILED", r.stderr[-2500:], flush=True)
        raise RuntimeError(label)
    print(f"{label}: {time.time() - t:.1f}s", flush=True)


def esc(s):
    return s.replace(":", "\\:").replace("'", "\u2019")


# ---------------------------------------------------------------- cards
def title_png(path, still, lines):
    bg = Image.open(still).convert("RGB").resize((1920, 1080)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.55)
    d = ImageDraw.Draw(bg)
    y = 430
    for text, size, font, color in lines:
        f = ImageFont.truetype(font, size)
        w = d.textlength(text, font=f)
        d.text(((1920 - w) / 2, y), text, font=f, fill=color)
        y += int(size * 1.35)
    bg.save(path)


def card_segment(png, out, secs, amb_start, fade_out=0.3):
    n = int(secs * 30)
    fc = (f"[0:v]fps=30,trim=end_frame={n},setpts=N/30/TB,scale=1920:1080:out_range=tv,setsar=1,"
          f"fade=t=in:st=0:d=0.4,fade=t=out:st={secs - fade_out}:d={fade_out},format=yuv420p[v];"
          f"[1:a]{NORM_A.format(ns=n * 1600)},volume=0.5,afade=t=in:d=0.5,afade=t=out:st={secs - fade_out}:d={fade_out}[a]")
    run(["-loop", "1", "-framerate", "30", "-t", str(secs + 0.2), "-i", png,
         "-ss", str(amb_start), "-t", str(secs + 0.3), "-i", SRC,
         "-filter_complex", fc, "-map", "[v]", "-map", "[a]"] + ENC + [out], "card " + os.path.basename(out))


def rank_png(path, still, rank, caption, sub):
    bg = Image.open(still).convert("RGB").resize((1920, 1080)).filter(ImageFilter.GaussianBlur(14))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.6)
    d = ImageDraw.Draw(bg)
    fr = ImageFont.truetype(FONT_B, 360)
    t = f"#{rank}"
    w = d.textlength(t, font=fr)
    d.text(((1920 - w) / 2, 200), t, font=fr, fill=(255, 255, 255))
    fc = ImageFont.truetype(FONT_B, 76)
    w = d.textlength(caption.upper(), font=fc)
    d.text(((1920 - w) / 2, 640), caption.upper(), font=fc, fill=(255, 255, 255))
    d.rectangle([(1920 - 140) // 2, 750, (1920 + 140) // 2, 758], fill=(255, 255, 255))
    fs = ImageFont.truetype(FONT_R, 40)
    w = d.textlength(sub, font=fs)
    d.text(((1920 - w) / 2, 785), sub, font=fs, fill=(215, 215, 215))
    bg.save(path)


def rank_card(png, out, secs, amb_start):
    n = int(secs * 30)
    fc = (f"[0:v]fps=30,trim=end_frame={n},setpts=N/30/TB,"
          f"scale=w='trunc(1920*(1.12-0.12*min(t/0.35,1)+0.04*t/{secs})/2)*2':h='trunc(1080*(1.12-0.12*min(t/0.35,1)+0.04*t/{secs})/2)*2':eval=frame,"
          f"crop=1920:1080:(iw-1920)/2:(ih-1080)/2,scale=1920:1080:out_range=tv,setsar=1,"
          f"fade=t=in:st=0:d=0.2,fade=t=out:st={secs - 0.18:.2f}:d=0.18:color=white,format=yuv420p[v];"
          f"[1:a]{NORM_A.format(ns=n * 1600)},volume=0.4,afade=t=in:d=0.2,afade=t=out:st={secs - 0.2:.2f}:d=0.2[a]")
    run(["-loop", "1", "-framerate", "30", "-t", str(secs + 0.2), "-i", png,
         "-ss", str(amb_start), "-t", str(secs + 0.3), "-i", SRC,
         "-filter_complex", fc, "-map", "[v]", "-map", "[a]"] + ENC + [out], "rank " + os.path.basename(out))


# ---------------------------------------------------------------- recap segments
def live_segment(out, start, end, tally_events, user_windows, fade_out=True):
    """tally_events: [(t_rel, text)] - text shown from t_rel on; user_windows: [(t0, t1)] rel times for BARAK tag."""
    n = int(round((end - start) * 30))
    d = n / 30
    v = NORM_V.format(n=n) + "," + GRADE + ",fade=t=in:st=0:d=0.15"
    if fade_out:
        v += f",fade=t=out:st={d - 0.15:.3f}:d=0.15"
    for i, (t0, text) in enumerate(tally_events):
        t1 = tally_events[i + 1][0] if i + 1 < len(tally_events) else 1e9
        v += f",drawtext={BOX}:x=48:y=h-text_h-60:text='{esc(text)}':enable='between(t,{t0:.3f},{t1 - 0.001:.3f})'"
    for t0, t1 in user_windows:
        v += f",drawtext={BOX}:x=48:y=h-text_h-150:text='BARAK':enable='between(t,{t0:.3f},{t1:.3f})'"
    v += ",format=yuv420p"
    a = NORM_A.format(ns=n * 1600) + f",afade=t=in:d=0.05,afade=t=out:st={d - 0.05:.3f}:d=0.05"
    run(["-ss", f"{start:.3f}", "-t", f"{d + 0.3:.3f}", "-i", SRC, "-filter_complex", f"[0:v]{v}[v];[0:a]{a}[a]",
         "-map", "[v]", "-map", "[a]"] + ENC + [out], "live " + os.path.basename(out))


def replay_geometry(m):
    rx, ry = RIM[m["hoop"]]
    sx, sy = m.get("shooter_xy") or (rx, ry + 200)
    if m["hoop"] == "A":
        sizes, push = [1280, 1440, 1600], 1.2
    elif m["hoop"] == "Bfar":
        sizes, push = [960, 1152, 1280], 1.25
    else:  # Bnear: rim at the frame edge -> centre on the shooter, no push
        sizes, push = [1280, 1440, 1600], 1.0
    for cw in sizes:
        ch = cw * 9 // 16
        if m["hoop"] == "Bnear":
            fx, fy = 0.5 * rx + 0.5 * sx, (ry + sy) / 2
        else:
            fx, fy = 0.6 * rx + 0.4 * sx, ry + ch / 6
        cx = int(max(0, min(1920 - cw, fx - cw / 2))) // 2 * 2
        cy = int(max(0, min(1080 - ch, fy - ch / 2))) // 2 * 2
        mx, my = 0.08 * cw, 0.08 * ch
        ok = all(cx + mx <= px <= cx + cw - mx and cy + my * 0.5 <= py <= cy + ch - my * 0.5
                 for px, py in [(rx, ry), (sx, sy)])
        if ok:
            break
    return cw, ch, cx, cy, push


def replay_segment(out, m):
    T = m["t_through"]
    pre = m.get("replay_pre", 2.0)
    post = 0.5
    cw, ch, cx, cy, push = replay_geometry(m)
    rx, ry = RIM[m["hoop"]]
    n_in = int(round((pre + post) * 30))
    n_out = n_in * 2
    dur = n_out / 30
    persp = ""
    if push > 1.0:
        tx = (rx - cx) * 1920 / cw
        ty = (ry - cy) * 1080 / ch
        z = f"(1+{push - 1:.4f}*(1-cos(PI*min(max(in-1,0)/{n_out},1)))/2)"
        L = f"max(0,min(W-W/{z},{tx:.1f}-W/{z}/2))"
        Tt = f"max(0,min(H-H/{z},{ty:.1f}-H/{z}/2))"
        persp = (f"perspective=eval=frame:interpolation=cubic:sense=source:x0='{L}':y0='{Tt}':x1='{L}+W/{z}':y1='{Tt}'"
                 f":x2='{L}':y2='{Tt}+H/{z}':x3='{L}+W/{z}':y3='{Tt}+H/{z}',")
    interp = ("framerate=fps=60,setpts=2*PTS,fps=30," if m.get("replay_blend")
              else "minterpolate=fps=60:mi_mode=mci,setpts=2*PTS,fps=30,")
    v = (NORM_V.format(n=n_in) + f",crop={cw}:{ch}:{cx}:{cy},hqdn3d=1.5:1.5:6:6," + interp +
         "scale=1920:1080:flags=lanczos," + persp + GRADE.replace("0.6:5:5:0", "0.8:5:5:0") + ",vignette=angle=PI/6,"
         f"tpad=stop_mode=clone:stop=6,trim=end_frame={n_out},setpts=N/30/TB,"
         "fade=t=in:st=0:d=0.2:color=white,"
         f"fade=t=out:st={dur - 0.15:.3f}:d=0.15,"
         f"drawtext=fontfile='{FF_FONT}':text='REPLAY':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:"
         f"boxborderw=10|18:x=w-text_w-60:y=56:enable='between(t,0.15,{dur - 0.2:.3f})',format=yuv420p")
    a = (NORM_A.format(ns=n_in * 1600) + ",atempo=0.5,volume=0.3,afade=t=in:d=0.2,"
         f"afade=t=out:st={dur - 0.4:.3f}:d=0.4,apad,atrim=end_sample={n_out * 1600},asetpts=N/SR/TB")
    graph = out + ".graph.txt"
    with open(graph, "w") as f:
        f.write(f"[0:v]{v}[v];[0:a]{a}[a]")
    run(["-ss", f"{T - pre:.3f}", "-t", f"{pre + post + 0.3:.3f}", "-i", SRC,
         "-/filter_complex", graph, "-map", "[v]", "-map", "[a]"] + ENC + [out], "replay " + os.path.basename(out))


def plan_recap(makes):
    """Group makes into live clips (merge overlapping windows) and build tally text."""
    teams_known = all(m["team"] in ("orange", "lime") for m in makes)
    tally = {"orange": 0, "lime": 0}
    clips = []
    for i, m in enumerate(makes):
        m["n"] = i + 1
        s, e = max(0.0, m["t_through"] - m.get("lead", LEAD)), m["t_through"] + TAIL
        # never cross the camera move
        su = next(x for x in bbconfig.SETUPS if x["name"] == bbconfig.setup_of(m["t_through"]))
        s = max(s, su["start"] + 0.5)
        if clips and s < clips[-1]["end"] and not clips[-1]["makes"][-1].get("replay"):
            clips[-1]["end"] = e
            clips[-1]["makes"].append(m)
        else:
            if clips and s < clips[-1]["end"]:  # quick score-back after a replay: pick up where live left off
                s = min(max(s, clips[-1]["end"]), m["t_through"] - 3.0)
            clips.append({"start": s, "end": e, "makes": [m]})
    for c in clips:
        ev = []
        uw = []
        for m in c["makes"]:
            if m["team"] in tally:
                tally[m["team"]] += 1
            # label by number + shooter (never a team tally); with a name in the label no separate user tag is needed
            ev.append((max(0.0, m["t_through"] - c["start"] - 0.2), f"BUCKET {m['n']}" + (f"   {m['name'].upper()}" if m.get("name") else "")))
            if m.get("is_user") and not m.get("name"):
                uw.append((max(0.0, m["t_release"] - c["start"] - 1.5), c["end"] - c["start"]))
        c["tally"] = ev
        c["user_windows"] = uw
    return clips, tally, teams_known


def concat_master(parts, out, share=True):
    lst = out + ".list.txt"
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vn",
                        "-af", "highpass=f=70,loudnorm=I=-14:TP=-2:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"highpass=f=70,loudnorm=I=-14:TP=-2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          "aresample=48000")
    master = out.replace(".mp4", "_master.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-movflags", "+faststart", master], "master " + os.path.basename(master))
    if share:
        run(["-i", master, "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M",
             "-g", "60", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1", "-color_range", "tv",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "copy",
             "-movflags", "+faststart", out], "share " + os.path.basename(out))
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "null", "-"], capture_output=True, text=True)
    print("decode check:", "clean" if not r.stderr.strip() else r.stderr[:500])


def recap(makes_path, out, top=False):
    makes = json.load(open(makes_path))
    if not top:
        makes = sorted(makes, key=lambda m: m["t_through"])
    work = os.path.join(WORK, "top5" if top else "recap")
    os.makedirs(work, exist_ok=True)
    if top:
        clips = []
        for m in makes:
            s0 = max(next(x for x in bbconfig.SETUPS if x["name"] == bbconfig.setup_of(m["t_through"]))["start"] + 0.5, m["t_through"] - LEAD)
            c = {"start": s0, "end": m["t_through"] + TAIL, "makes": [m]}
            label = f"#{m['rank']}   {m['caption'].upper()}"
            c["tally"] = [(0.0, label)]
            c["user_windows"] = [(0.0, c["end"] - s0)] if m.get("is_user") else []
            clips.append(c)
        tally, teams_known = {}, False
    else:
        clips, tally, teams_known = plan_recap(makes)
    jobs = []  # (index, kind, args)
    still = os.path.join(work, "still.png")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{makes[len(makes) // 2]['t_through'] - 3:.2f}", "-i", SRC, "-frames:v", "1", still])
    title_png(os.path.join(work, "title.png"), still, [
        (f"TOP {len(makes)} BUCKETS" if top else TITLE, 130, FONT_B, (255, 255, 255)),
        (f"{DATE}  |  " + ("Pickup run" if top else "Every basket"), 46, FONT_R, (230, 230, 230))])
    sub = (f"{DATE}  |  Pickup run" if top else f"{len(makes)} baskets  |  {DATE}")
    end_lines = [("THAT'S THE RUN", 110, FONT_B, (255, 255, 255)), (sub, 46, FONT_R, (230, 230, 230))]
    if top and os.environ.get("MUSIC_CREDIT"):
        end_lines.append((os.environ["MUSIC_CREDIT"], 30, FONT_R, (190, 190, 190)))
    title_png(os.path.join(work, "end.png"), still, end_lines)
    parts = [os.path.join(work, "s000_title.mov")]
    jobs.append(lambda: card_segment(os.path.join(work, "title.png"), parts[0], 3.0, max(0, makes[0]["t_through"] - 12)))
    k = 1
    for c in clips:
        last = c["makes"][-1]
        if top:
            rs = os.path.join(work, f"s{k:03d}_rankstill.png")
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{last['t_through']:.2f}", "-i", SRC, "-frames:v", "1", rs])
            rp_png = os.path.join(work, f"s{k:03d}_rank.png")
            rank_png(rp_png, rs, last["rank"], last["caption"], last["sub"])
            rc = os.path.join(work, f"s{k:03d}_rank.mov"); k += 1
            parts.append(rc)
            jobs.append((lambda rp_png=rp_png, rc=rc, c=c: rank_card(rp_png, rc, 1.6, c["start"])))
        lp = os.path.join(work, f"s{k:03d}_live.mov"); k += 1
        parts.append(lp)
        jobs.append((lambda c=c, lp=lp, last=last: live_segment(lp, c["start"], c["end"], c["tally"], c["user_windows"],
                                                                 fade_out=not last.get("replay"))))
        if last.get("replay"):
            rp = os.path.join(work, f"s{k:03d}_replay.mov"); k += 1
            parts.append(rp)
            jobs.append((lambda last=last, rp=rp: replay_segment(rp, last)))
    endp = os.path.join(work, f"s{k:03d}_end.mov")
    parts.append(endp)
    jobs.append(lambda: card_segment(os.path.join(work, "end.png"), endp, 5.0, min(bbconfig.SETUPS[-1]["end"] - 6, makes[-1]["t_through"] + 3), fade_out=1.0))
    with ThreadPoolExecutor(int(os.environ.get("RENDER_WORKERS", "4"))) as ex:
        list(ex.map(lambda f: f(), jobs))
    json.dump({"clips": [{"start": c["start"], "end": c["end"], "n": len(c["makes"])} for c in clips], "tally": tally},
              open(os.path.join(work, "plan.json"), "w"), indent=1)
    concat_master(parts, out)
    print("clips", len(clips), "makes", len(makes), "replays", sum(1 for m in makes if m.get("replay")), "tally", tally)


def reel(clips_path, out):
    clips = sorted(json.load(open(clips_path)), key=lambda c: c["start"])
    work = os.path.join(WORK, "reel")
    os.makedirs(work, exist_ok=True)
    parts, jobs = [], []
    for i, c in enumerate(clips):
        p = os.path.join(work, f"r{i:03d}.mov")
        parts.append(p)
        n = int(round((c["end"] - c["start"]) * 30))
        d = n / 30
        fc = (f"[0:v]{NORM_V.format(n=n)},format=yuv420p[v];"
              f"[0:a]{NORM_A.format(ns=n * 1600)},afade=t=in:d=0.05,afade=t=out:st={d - 0.05:.3f}:d=0.05[a]")
        jobs.append(lambda c=c, p=p, fc=fc, d=d: run(["-ss", f"{c['start']:.3f}", "-t", f"{d + 0.3:.3f}", "-i", SRC,
                                                      "-filter_complex", fc, "-map", "[v]", "-map", "[a]"] + ENC + [p],
                                                     "reel " + os.path.basename(p)))
    with ThreadPoolExecutor(int(os.environ.get("RENDER_WORKERS", "4"))) as ex:
        list(ex.map(lambda f: f(), jobs))
    concat_master(parts, out)
    print("reel clips", len(clips), "total", round(sum(c["end"] - c["start"] for c in clips), 1), "s")


if __name__ == "__main__":
    mode, src, out = sys.argv[1:4]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    {"recap": recap, "reel": reel, "top5": lambda a, b: recap(a, b, top=True)}[mode](src, out)

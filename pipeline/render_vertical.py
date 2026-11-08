"""LEGACY fixed-crop vertical Top N. Barak rejected it on 09.10.2026 ("doesn't catch the whole action. I expect the trim
to move with the ball"): use render_vertical_follow.py, which imports the card / overlay helpers from this file.
Running this file directly needs an explicit --static flag.

Vertical (1080x1920) Top 5 from the landscape Top 5 intermediates.

Layout per play: blurred, darkened full frame fills the canvas; a 4:5 crop of the action
(centred between rim and shooter) sits in the middle (y 285-1635); rank + caption live in
the top/bottom bands. Cards (title, #N, end) are rebuilt for portrait.
  python render_vertical.py data/top5.json output/Top5_Baskets_Vertical.mp4
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_v2 import RIM, ENC, run, replay_geometry, FONT_B, FONT_R, WORK, DATE
N = 5

SEG = os.path.join(WORK, "top5")
OUT = os.path.join(WORK, "vertical")
MUSIC = os.path.join(os.path.dirname(WORK), "music", "Hitman.mp3")
CREDIT = "Music: Hitman by Kevin MacLeod (incompetech.com), CC BY 4.0"
W, H, FW, FH, FY = 1080, 1920, 1080, 1350, 285


def f(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def centred(d, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w_
    lines.append(cur)
    return lines


def overlay_png(path, m, replay):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    centred(d, 58, f"TOP {N} BUCKETS", f(34), (210, 210, 210, 255))
    centred(d, 100, f"#{m['rank']}", f(150), (255, 255, 255, 255))
    y = 1668
    for line in wrap(d, m["caption"].upper(), f(58), W - 120):
        centred(d, y, line, f(58), (255, 255, 255, 255)); y += 70
    centred(d, y + 12, m["sub"], f(36, False), (215, 215, 215, 255))
    if replay:
        t = "REPLAY"
        tw = d.textlength(t, font=f(34))
        d.rectangle([W - tw - 76, FY + 30, W - 40, FY + 82], fill=(0, 0, 0, 150))
        d.text((W - tw - 58, FY + 34), t, font=f(34), fill=(255, 255, 255, 255))
    im.save(path)


def card_png(path, still, lines):
    bg = Image.open(still).convert("RGB")
    s = H / bg.height
    bg = bg.resize((int(bg.width * s), H)).crop((0, 0, W, H)) if False else bg.resize((int(bg.width * s), H))
    x0 = (bg.width - W) // 2
    bg = bg.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.58)
    d = ImageDraw.Draw(bg)
    total = sum(sz * 1.25 for _, sz, _, _ in lines)
    y = (H - total) / 2
    for text, sz, bold, col in lines:
        for line in wrap(d, text, f(sz, bold), W - 110):
            centred(d, y, line, f(sz, bold), col); y += sz * 1.25
    bg.save(path)


def play_segment(src, png, out, fx, replay=False):
    X = int(max(0, min(1920 - 864, fx - 432))) // 2 * 2
    # landscape replays carry their own REPLAY tag (top-right); erase it, the portrait overlay adds one
    pre = "delogo=x=1680:y=34:w=224:h=80," if replay else ""
    fc = (f"[0:v]{pre}split[a][b];"
          f"[a]scale=-2:{H},crop={W}:{H}:(iw-{W})/2:0,boxblur=24:2,eq=brightness=-0.12:saturation=0.8[bg];"
          f"[b]crop=864:1080:{X}:0,scale={FW}:{FH}:flags=lanczos[fg];"
          f"[bg][fg]overlay=0:{FY}[c];[c][1:v]overlay=0:0,format=yuv420p[v]")
    run(["-i", src, "-loop", "1", "-i", png, "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-shortest"] + ENC + [out],
        "vplay " + os.path.basename(out))


def card_segment(png, audio_src, out, secs, fade_out, white=False):
    n = int(secs * 30)
    col = ":color=white" if white else ""
    fc = (f"[0:v]fps=30,trim=end_frame={n},setpts=N/30/TB,"
          f"scale=w='trunc({W}*(1.1-0.1*min(t/0.35,1)+0.04*t/{secs})/2)*2':h='trunc({H}*(1.1-0.1*min(t/0.35,1)+0.04*t/{secs})/2)*2':eval=frame,"
          f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,setsar=1,fade=t=in:st=0:d=0.25,fade=t=out:st={secs - fade_out:.2f}:d={fade_out}{col},format=yuv420p[v]")
    run(["-loop", "1", "-framerate", "30", "-t", str(secs + 0.2), "-i", png, "-i", audio_src,
         "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-t", f"{n / 30:.3f}"] + ENC + [out], "vcard " + os.path.basename(out))


def main():
    global N
    top = json.load(open(sys.argv[1]))
    N = len(top)
    out = sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    still = os.path.join(SEG, "still.png")
    jobs, parts = [], []
    tp = os.path.join(OUT, "title.png")
    card_png(tp, still, [(f"TOP {N}", 230, True, (255, 255, 255)), ("BUCKETS", 120, True, (255, 255, 255)),
                         (f"Pickup run  |  {DATE}", 44, False, (225, 225, 225))])
    p = os.path.join(OUT, "v000_title.mov"); parts.append(p)
    jobs.append(lambda p=p: card_segment(tp, os.path.join(SEG, "s000_title.mov"), p, 3.0, 0.3))
    for i, m in enumerate(top):
        b = 1 + 3 * i
        rk = os.path.join(OUT, f"rank{i}.png")
        card_png(rk, os.path.join(SEG, f"s{b:03d}_rankstill.png"),
                 [(f"#{m['rank']}", 420, True, (255, 255, 255)), (m["caption"].upper(), 60, True, (255, 255, 255)),
                  (m["sub"], 42, False, (220, 220, 220))])
        p = os.path.join(OUT, f"v{b:03d}_rank.mov"); parts.append(p)
        jobs.append(lambda rk=rk, b=b, p=p: card_segment(rk, os.path.join(SEG, f"s{b:03d}_rank.mov"), p, 1.6, 0.18, white=True))
        rx, ry = RIM[m["hoop"]]
        sx, sy = m.get("shooter_xy") or (rx, ry + 200)
        ol = os.path.join(OUT, f"ol{i}_live.png"); overlay_png(ol, m, False)
        p = os.path.join(OUT, f"v{b + 1:03d}_live.mov"); parts.append(p)
        jobs.append(lambda ol=ol, b=b, p=p, fx=0.6 * rx + 0.4 * sx: play_segment(os.path.join(SEG, f"s{b + 1:03d}_live.mov"), ol, p, fx))
        cw, ch, cx, cy, push = replay_geometry(m)
        ro, so = (rx - cx) * 1920 / cw, (sx - cx) * 1920 / cw
        orp = os.path.join(OUT, f"ol{i}_replay.png"); overlay_png(orp, m, True)
        p = os.path.join(OUT, f"v{b + 2:03d}_replay.mov"); parts.append(p)
        jobs.append(lambda orp=orp, b=b, p=p, fx=0.6 * ro + 0.4 * so: play_segment(os.path.join(SEG, f"s{b + 2:03d}_replay.mov"), orp, p, fx, replay=True))
    ep = os.path.join(OUT, "end.png")
    card_png(ep, still, [("THAT'S THE RUN", 110, True, (255, 255, 255)), (f"Pickup run  |  {DATE}", 44, False, (225, 225, 225)),
                         (CREDIT, 30, False, (190, 190, 190))])
    p = os.path.join(OUT, f"v{1 + 3 * len(top):03d}_end.mov"); parts.append(p)
    jobs.append(lambda p=p: card_segment(ep, os.path.join(SEG, f"s{1 + 3 * len(top):03d}_end.mov"), p, 5.0, 1.0))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda j: j(), jobs))
    lst = os.path.join(OUT, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{x}'\n" for x in parts)
    joined = os.path.join(OUT, "joined.mov")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], "concat")
    D = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", joined],
                             capture_output=True, text=True).stdout)
    fc = (f"[0:a]volume=0.45[g];[1:a]atrim=0:{D:.3f},asetpts=N/SR/TB,volume=0.55,afade=t=in:d=1.0,"
          f"afade=t=out:st={D - 2.5:.3f}:d=2.5[m];[g][m]amix=inputs=2:duration=first:normalize=0,"
          f"loudnorm=I=-14:TP=-2:LRA=11,aresample=48000[a]")
    run(["-i", joined, "-i", MUSIC, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
         "-crf", "22", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", out], "final")
    run(["-i", out, "-vf", "scale=720:1280", "-c:v", "libx264", "-preset", "medium", "-b:v", "2300k", "-maxrate", "3000k",
         "-bufsize", "6000k", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out.replace(".mp4", "_phone.mp4")], "phone")
    print("done", D)


if __name__ == "__main__":
    if "--static" not in sys.argv:
        raise SystemExit("render_vertical.py is the rejected fixed-crop cut. Use render_vertical_follow.py "
                         "(the window follows the ball); pass --static only if a fixed crop is really wanted.")
    sys.argv.remove("--static")
    main()

"""Build labelled contact sheets from the game video for visual review.

Usage:
  python sheet.py --start 425 --end 431 --fps 5 --out out.jpg
                  [--crop x0,y0,x1,y1] [--cols 4] [--tile-w 640] [--hires]

Without --hires, frames come from the 5 fps full-res dump (fast, fps <= 5).
With --hires, frames are decoded straight from the source video, so any fps
up to 30 works (use for shot / rim close-ups).
Every tile is stamped with its video time as m:ss.s (and frame index at 30fps).
"""
import argparse, os, subprocess, tempfile, glob, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbconfig import VIDEO, F5


def fmt(t):
    m = int(t // 60)
    return f"{m}:{t - 60 * m:04.1f}"


def load_f5(t):
    k = int(round(t * 5)) + 1
    p = os.path.join(F5, f"{k:05d}.jpg")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


def load_hires(start, end, fps, crop):
    tmp = tempfile.mkdtemp()
    vf = [f"fps={fps}"]
    if crop:
        x0, y0, x1, y1 = crop
        vf.insert(0, f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0}")
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", VIDEO, "-t", f"{end - start:.3f}",
                    "-vf", ",".join(vf), "-q:v", "2", os.path.join(tmp, "%04d.jpg")], check=True)
    files = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
    return [(start + i / fps, Image.open(f).convert("RGB")) for i, f in enumerate(files)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--fps", type=float, default=5)
    ap.add_argument("--crop", type=str, default=None)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--tile-w", type=int, default=640)
    ap.add_argument("--hires", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None

    tiles = []
    if a.hires:
        tiles = load_hires(a.start, a.end, a.fps, crop)
    else:
        step = 1.0 / min(a.fps, 5)
        t = a.start
        while t < a.end - 1e-6:
            im = load_f5(t)
            if im is not None:
                if crop:
                    im = im.crop(crop)
                tiles.append((t, im))
            t += step
    if not tiles:
        raise SystemExit("no frames")
    w0, h0 = tiles[0][1].size
    tw = a.tile_w
    th = int(round(h0 * tw / w0))
    cols = a.cols
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), "black")
    fs = max(14, tw // 22)
    try:
        font = ImageFont.truetype("arialbd.ttf", fs)
    except OSError:
        font = ImageFont.load_default()
    for i, (t, im) in enumerate(tiles):
        im = im.resize((tw, th), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        lab = f"{fmt(t)}  f{int(round(t * 30))}"
        bw = d.textlength(lab, font=font)
        d.rectangle([0, 0, bw + 8, fs + 6], fill="black")
        d.text((4, 2), lab, fill="yellow", font=font)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(a.out, quality=88)
    print(a.out, len(tiles), sheet.size)


if __name__ == "__main__":
    main()

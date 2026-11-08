"""Simulation stills with the lines drawn by Weavy (Barak: "you can also draw lines with it"; the test on 2026-10-12 worked).

  python weavy_still.py prep <sim spec json> <id> [x0 y0 x1 y1]
      -> work/weavy/tele/<id>_plain.png   the composite without drawings, 16:9, 2048x1152   (image 1 for the tool)
         work/weavy/tele/<id>_guide.png   the same with our arrows, zones and rings, no text  (image 2 for the tool)
         work/weavy/tele/<id>_meta.json   the crop and the Hebrew labels, for the finish step
  python weavy_still.py finish <id> <weavy output image> <out still jpg>
      -> the tool's picture at 1920x1080 with the Hebrew labels put back on top (the tool is told to write no text)
  python weavy_still.py panel <id> <finished still jpg> <out panel jpg>
      -> the two-up for the review card: the real frame with our drawings next to the finished still

The crop is the spec's panel crop widened to 16:9, unless four numbers are given. Only simulation stills go through the tool;
real footage is never redrawn.
"""
import json, os, sys
from PIL import Image, ImageDraw
import make_weavy_sim as S

HERE = os.path.dirname(os.path.abspath(__file__))
TELE = os.path.join(HERE, "work", "weavy", "tele")
os.makedirs(TELE, exist_ok=True)
PROMPT = ("Image 1 is a still frame from a phone video of a pickup basketball game on an outdoor court at night. Image 2 is the same "
          "frame with rough coaching marks drawn on it: green arrows, green shaded areas on the floor and red circles around some "
          "players. Reproduce image 1 exactly, with every player, every colour, the court lines and the background unchanged and in "
          "the same positions, and add the marks of image 2 as clean TV-broadcast telestration in the same places: each green arrow "
          "as a thick bright-green arrow painted flat on the court floor with a soft glow, each green area as translucent green "
          "shading on the floor, each red circle as a thin red ring around the same player. No text and no other marks. Do not "
          "move, add, remove or restyle anyone, and keep every player's clothes exactly as in image 1.")

cmd = sys.argv[1]
if cmd == "prep":
    spec = json.load(open(sys.argv[2], encoding="utf-8")); sid = sys.argv[3]
    if len(sys.argv) >= 8:
        x0, y0, x1, y1 = (int(a) for a in sys.argv[4:8])
    else:
        x0, y0, x1, y1 = spec["panel"]["crop"]
    w = x1 - x0; h = int(round(w * 9 / 16)); cy = (y0 + y1) / 2
    ty0 = int(max(0, min(1080 - h, cy - h / 2))); box = (x0, ty0, x0 + w, ty0 + h)
    base = Image.open(os.path.join(HERE, spec["out"])).convert("RGB")
    guide = S.annotate(base, spec.get("zones", []), spec.get("arrows", []), spec.get("rings", []), ())
    base.crop(box).resize((2048, 1152), Image.LANCZOS).save(os.path.join(TELE, f"{sid}_plain.png"))
    guide.crop(box).resize((2048, 1152), Image.LANCZOS).save(os.path.join(TELE, f"{sid}_guide.png"))
    json.dump({"id": sid, "spec": sys.argv[2], "box": box, "labels": spec.get("labels", [])}, open(os.path.join(TELE, f"{sid}_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("prepared", sid, "crop", box, "| labels", len(spec.get("labels", [])))
elif cmd == "finish":
    sid, src, out = sys.argv[2], sys.argv[3], sys.argv[4]
    meta = json.load(open(os.path.join(TELE, f"{sid}_meta.json"), encoding="utf-8"))
    x0, y0, x1, y1 = meta["box"]; s = 1920 / (x1 - x0)
    im = Image.open(src).convert("RGB").resize((1920, 1080), Image.LANCZOS).convert("RGBA")
    over = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
    for lb in meta["labels"]:
        size = int(round(lb.get("size", 28) * s))
        x, y = (lb["at"][0] - x0) * s, (lb["at"][1] - y0) * s
        S.text(d, (x, max(96, min(1080 - size - 24, y))), lb["text"], size=size, anchor=lb.get("anchor", "l"))
    Image.alpha_composite(im, over).convert("RGB").save(out, quality=92)
    print("wrote", out)
elif cmd == "panel":
    # two-up for the review card: what really happened (our drawings on the real frame) next to the finished still
    sid, still, out = sys.argv[2], sys.argv[3], sys.argv[4]
    meta = json.load(open(os.path.join(TELE, f"{sid}_meta.json"), encoding="utf-8"))
    spec = json.load(open(os.path.join(HERE, meta["spec"]) if not os.path.isabs(meta["spec"]) else meta["spec"], encoding="utf-8"))
    pn = spec["panel"]
    real = S.annotate(S.frame(pn.get("real_reel", spec["frame_reel"])), (), pn.get("real_arrows", []), pn.get("real_rings", []), pn.get("real_labels", []))
    W, H = 1080, 608
    left = real.crop(tuple(meta["box"])).resize((W, H), Image.LANCZOS); right = Image.open(still).convert("RGB").resize((W, H), Image.LANCZOS)
    panel = Image.new("RGB", (W * 2 + 24, H + 64), S.NAVY); dp = ImageDraw.Draw(panel)
    panel.paste(left, (0, 64)); panel.paste(right, (W + 24, 64))
    S.text(dp, (W // 2, 14), pn.get("left_title", ""), size=30, box=S.NAVY + (255,), anchor="c")
    S.text(dp, (W + 24 + W // 2, 14), pn.get("right_title", ""), size=30, box=S.NAVY + (255,), anchor="c")
    panel.save(out, quality=90)
    print("wrote", out, panel.size)
elif cmd == "prompt":
    print(PROMPT)

"""16:9 still of a simulation composite, for the end of a coaching video.

  python make_sim_still.py work/weavy/sim_<id>.json <out.jpg> [--plain]
Takes the panel crop of the spec, widens it to 16:9 around the same centre and scales the annotated composite to 1920x1080.
--plain uses the composite without the drawings (work/weavy/sim_<id>.png) instead of the annotated one.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
spec_path, out = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path, encoding="utf-8"))
src = os.path.join(HERE, spec["out"]) if "--plain" in sys.argv else os.path.join(HERE, spec["out"].rsplit(".", 1)[0] + "_annotated.jpg")
x0, y0, x1, y1 = spec["panel"]["crop"]
w = x1 - x0; h = int(round(w * 9 / 16)); cy = (y0 + y1) / 2
if h > 1080:
    h = 1080; w = 1920; x0 = 0
ty0 = int(max(0, min(1080 - h, cy - h / 2)))
box = (x0, ty0, x0 + w, ty0 + h)
Image.open(src).convert("RGB").crop(box).resize((1920, 1080), Image.LANCZOS).save(out, quality=92)
print("wrote", out, "from", os.path.basename(src), "crop", box)

"""Per-game configuration shared by every pipeline tool.

The game folder (env BB_GAME, default: current directory) holds game.json:
{
  "video": "C:/.../VID.mp4",
  "work":  "C:/.../scratch/<game>",            # big intermediates (5 fps frames, renders)
  "date":  "23.09.2026",
  "title": "PICKUP RUN",
  "user":  {"name": "Barak", "team_color": "orange",
            "look": "bald, orange pinnie over navy T-shirt, dark shorts, maroon shoes"},
  "setups": [                                  # one entry per camera position, in time order
    {"name": "A", "start": 0,   "end": 968,  "court": "half", "hoops": ["A"]},
    {"name": "B", "start": 981, "end": 1912, "court": "full", "hoops": ["Bnear", "Bfar"]}
  ],
  "hoops": {                                   # full-frame pixels, 1920x1080
    "A": {"rim": [1290, 458], "rim_y": 458, "net": [1255, 1305, 512], "roi": [1180, 330, 1400, 560],
          "strip_crop": [1150, 300, 1430, 580], "ctx_crop": null, "small": false}
  }
}
"""
import json, os

GAME_DIR = os.environ.get("BB_GAME") or os.getcwd()
_path = os.path.join(GAME_DIR, "game.json")
CFG = json.load(open(_path, encoding="utf-8"))
VIDEO = CFG["video"]
WORK = CFG["work"]
F5 = os.path.join(WORK, "f5")
HOOPS = CFG["hoops"]
SETUPS = CFG["setups"]
RIM = {k: tuple(v["rim"]) for k, v in HOOPS.items()}
PIPELINE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(WORK, exist_ok=True)


def setup_of(t):
    """Name of the camera setup covering time t, or None (camera moving / dead time)."""
    for s in SETUPS:
        if s["start"] <= t < s["end"]:
            return s["name"]
    return None


def setup_of_hoop(h):
    return next(s for s in SETUPS if h in s["hoops"])


def data(*p):
    os.makedirs(os.path.join(GAME_DIR, "data"), exist_ok=True)
    return os.path.join(GAME_DIR, "data", *p)

"""Draw a stick-figure pose rig for the Weavy image tool: body, ball and which side of the body each limb is on.

  python make_pose_rig.py --builtin <pose> <out.png> [size]
  python make_pose_rig.py <pose.json> <out.png> [size]

Colour code (also spelled out in the prompt sent with the rig):
  bright green bones + dots  = spine, head and the limbs on the side NEAREST the camera
  pale green bones + dots    = the limbs on the FAR side of the body (drawn first, so they sit behind)
  orange dots                = hands and feet (pale orange on the far side)
  purple circle              = the basketball, at its real position relative to the body

pose.json: {"facing": "right" | "left",
            "joints": {"head", "neck", "pelvis", "near_elbow", "near_hand", "far_elbow", "far_hand",
                       "near_knee", "near_foot", "far_knee", "far_foot"},     # [x, y] in body heights, floor at y = 0
            "ball": [x, y]}                                                   # optional
Poses are defined facing right; "facing": "left" mirrors the drawing.
"""
import json, math, sys
from PIL import Image, ImageDraw

GREEN, PALE_GREEN = (62, 230, 176), (176, 240, 220)
ORANGE, PALE_ORANGE = (255, 122, 47), (255, 196, 160)
PURPLE = (122, 63, 228)
BALL_R = 0.068          # ball radius in body heights (24 cm ball, 1.78 m player)


def pol(p, length, deg):
    """point at `length` from p; deg measured from straight down, positive toward the facing direction (+x); 180 = straight up"""
    a = math.radians(deg)
    return [p[0] + length * math.sin(a), p[1] - length * math.cos(a)]


def _ground(j, ball=None, floor=0.03):
    """shift the pose so the lower foot rests on the floor"""
    dy = floor - min(j["near_foot"][1], j["far_foot"][1])
    for k in j:
        j[k] = [j[k][0], j[k][1] + dy]
    return j, ([ball[0], ball[1] + dy] if ball else None)


def drive_near_hand():
    """Low explosive first step, ball in the NEAR hand (a right-hand drive when facing right), far forearm up as a shield."""
    pelvis = [0.0, 0.44]; lean = math.radians(42)
    neck = [pelvis[0] + 0.30 * math.sin(lean), pelvis[1] + 0.30 * math.cos(lean)]
    head = pol(neck, 0.115, 180 - 22)
    j = {"head": head, "neck": neck, "pelvis": pelvis}
    j["near_knee"] = pol(pelvis, 0.25, 62); j["near_foot"] = pol(j["near_knee"], 0.26, -8)
    j["far_knee"] = pol(pelvis, 0.25, -28); j["far_foot"] = pol(j["far_knee"], 0.26, -62)
    j["near_elbow"] = pol(neck, 0.17, 28); j["near_hand"] = pol(j["near_elbow"], 0.15, 48)
    j["far_elbow"] = pol(neck, 0.17, 66); j["far_hand"] = pol(j["far_elbow"], 0.15, 112)
    ball = [j["near_hand"][0] + 0.03, j["near_hand"][1] - 0.12]
    j, ball = _ground(j, ball)
    return {"facing": "right", "joints": j, "ball": ball}


def drive_far_hand():
    """Low explosive first step, ball in the FAR hand (a left-hand drive when facing right): the near leg steps across,
    the near forearm is up as a shield between the defender and the ball."""
    pelvis = [0.0, 0.44]; lean = math.radians(42)
    neck = [pelvis[0] + 0.30 * math.sin(lean), pelvis[1] + 0.30 * math.cos(lean)]
    head = pol(neck, 0.115, 180 - 22)
    j = {"head": head, "neck": neck, "pelvis": pelvis}
    j["near_knee"] = pol(pelvis, 0.25, 62); j["near_foot"] = pol(j["near_knee"], 0.26, -8)       # near leg steps across in front
    j["far_knee"] = pol(pelvis, 0.25, -28); j["far_foot"] = pol(j["far_knee"], 0.26, -62)
    j["far_elbow"] = pol(neck, 0.17, 30); j["far_hand"] = pol(j["far_elbow"], 0.15, 52)           # far arm reaches down to the ball
    j["near_elbow"] = pol(neck, 0.17, 58); j["near_hand"] = pol(j["near_elbow"], 0.15, 118)       # near forearm across the chest
    ball = [j["far_hand"][0] + 0.03, j["far_hand"][1] - 0.12]
    j, ball = _ground(j, ball)
    return {"facing": "right", "joints": j, "ball": ball}


def set_shot():
    """Jump shot at the set point, feet still on the floor: upright, knees a little bent, ball above the forehead in the
    near (shooting) hand, far hand on the side of the ball."""
    pelvis = [0.0, 0.50]; lean = math.radians(4)
    neck = [pelvis[0] + 0.30 * math.sin(lean), pelvis[1] + 0.30 * math.cos(lean)]
    head = pol(neck, 0.115, 180 + 4)
    j = {"head": head, "neck": neck, "pelvis": pelvis}
    j["near_knee"] = pol(pelvis, 0.25, 16); j["near_foot"] = pol(j["near_knee"], 0.26, -12)
    j["far_knee"] = pol(pelvis, 0.25, 6); j["far_foot"] = pol(j["far_knee"], 0.26, -16)
    j["near_elbow"] = pol(neck, 0.17, 104); j["near_hand"] = pol(j["near_elbow"], 0.15, 170)      # upper arm forward, forearm up
    j["far_elbow"] = pol(neck, 0.17, 84); j["far_hand"] = pol(j["far_elbow"], 0.15, 158)
    ball = [j["near_hand"][0] + 0.015, j["near_hand"][1] + 0.075]
    j, ball = _ground(j, ball)
    return {"facing": "right", "joints": j, "ball": ball}


def kick_out_pass():
    """Two-hand chest pass off a jump stop: both feet planted wide, knees bent, both arms extended, ball just leaving the
    hands. Defined facing right; drawn facing LEFT (a pass back out to the top of the arc)."""
    pelvis = [0.0, 0.46]; lean = math.radians(14)
    neck = [pelvis[0] + 0.30 * math.sin(lean), pelvis[1] + 0.30 * math.cos(lean)]
    head = pol(neck, 0.115, 180 - 8)
    j = {"head": head, "neck": neck, "pelvis": pelvis}
    j["near_knee"] = pol(pelvis, 0.25, 34); j["near_foot"] = pol(j["near_knee"], 0.26, -6)
    j["far_knee"] = pol(pelvis, 0.25, -24); j["far_foot"] = pol(j["far_knee"], 0.26, -14)
    j["near_elbow"] = pol(neck, 0.17, 72); j["near_hand"] = pol(j["near_elbow"], 0.15, 96)
    j["far_elbow"] = pol(neck, 0.17, 80); j["far_hand"] = pol(j["far_elbow"], 0.15, 100)
    ball = [j["near_hand"][0] + 0.09, (j["near_hand"][1] + j["far_hand"][1]) / 2]
    j, ball = _ground(j, ball)
    return {"facing": "left", "joints": j, "ball": ball}


def drive_past_hip():
    """Second stride of a drive, already level with the defender: the FAR leg lands long in front, the near leg pushes off behind,
    the ball is pushed ahead at knee height in the NEAR hand (away from the defender), the far shoulder and forearm lead."""
    pelvis = [0.0, 0.47]; lean = math.radians(38)
    neck = [pelvis[0] + 0.30 * math.sin(lean), pelvis[1] + 0.30 * math.cos(lean)]
    head = pol(neck, 0.115, 180 - 20)
    j = {"head": head, "neck": neck, "pelvis": pelvis}
    j["far_knee"] = pol(pelvis, 0.25, 70); j["far_foot"] = pol(j["far_knee"], 0.26, 4)          # far leg lands in front
    j["near_knee"] = pol(pelvis, 0.25, -34); j["near_foot"] = pol(j["near_knee"], 0.26, -76)    # near leg pushes off behind
    j["near_elbow"] = pol(neck, 0.17, 22); j["near_hand"] = pol(j["near_elbow"], 0.15, 62)      # near arm pushes the ball ahead
    j["far_elbow"] = pol(neck, 0.17, 78); j["far_hand"] = pol(j["far_elbow"], 0.15, 104)        # far forearm leads as a shield
    ball = [j["near_hand"][0] + 0.06, j["near_hand"][1] - 0.11]
    j, ball = _ground(j, ball)
    return {"facing": "right", "joints": j, "ball": ball}


def pass_near_side():
    """One-hand push pass made off a live dribble toward the viewer (his right when he faces right): body still moving right,
    chest and head turned to the viewer, the NEAR arm extended at the viewer (foreshortened in a side view), ball just released."""
    pelvis = [0.0, 0.49]; lean = math.radians(14)
    neck = [pelvis[0] + 0.30 * math.sin(lean), pelvis[1] + 0.30 * math.cos(lean)]
    head = pol(neck, 0.115, 180 - 4)
    j = {"head": head, "neck": neck, "pelvis": pelvis}
    j["near_knee"] = pol(pelvis, 0.25, 30); j["near_foot"] = pol(j["near_knee"], 0.26, -10)
    j["far_knee"] = pol(pelvis, 0.25, -16); j["far_foot"] = pol(j["far_knee"], 0.26, -42)
    j["near_elbow"] = pol(neck, 0.09, 24); j["near_hand"] = pol(j["near_elbow"], 0.08, 34)      # short: the arm points at the viewer
    j["far_elbow"] = pol(neck, 0.17, 28); j["far_hand"] = pol(j["far_elbow"], 0.15, 74)
    ball = [j["near_hand"][0] + 0.03, j["near_hand"][1] - 0.02]
    j, ball = _ground(j, ball)
    return {"facing": "right", "joints": j, "ball": ball}


POSES = {"drive_near_hand": drive_near_hand, "drive_tight": drive_near_hand, "drive_far_hand": drive_far_hand,
         "set_shot": set_shot, "kick_out_pass": kick_out_pass, "drive_past_hip": drive_past_hip, "pass_near_side": pass_near_side}
FAR = [("neck", "far_elbow"), ("far_elbow", "far_hand"), ("pelvis", "far_knee"), ("far_knee", "far_foot")]
MID = [("head", "neck"), ("neck", "pelvis")]
NEAR = [("neck", "near_elbow"), ("near_elbow", "near_hand"), ("pelvis", "near_knee"), ("near_knee", "near_foot")]


def draw(pose, out, size=1024, margin=0.13):
    J = {k: list(v) for k, v in pose["joints"].items()}
    ball = list(pose["ball"]) if pose.get("ball") else None
    if pose.get("facing") == "left":
        J = {k: [-v[0], v[1]] for k, v in J.items()}
        ball = [-ball[0], ball[1]] if ball else None
    xs = [p[0] for p in J.values()] + ([ball[0] - BALL_R, ball[0] + BALL_R] if ball else [])
    ys = [p[1] for p in J.values()] + ([ball[1] - BALL_R, ball[1] + BALL_R] if ball else [])
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    scale = size * (1 - 2 * margin) / max(w, h)
    ox = size / 2 - (min(xs) + w / 2) * scale
    oy = size / 2 + (min(ys) + h / 2) * scale
    P = {k: (ox + v[0] * scale, oy - v[1] * scale) for k, v in J.items()}
    im = Image.new("RGB", (size, size), "white"); d = ImageDraw.Draw(im)
    lw = max(10, int(size * 0.022)); r = int(lw * 1.05); ro = int(lw * 1.35)

    def bones(pairs, col, width):
        for a, b in pairs:
            d.line([P[a], P[b]], fill=col, width=width)

    def dot(k, col, rad):
        p = P[k]; d.ellipse([p[0] - rad, p[1] - rad, p[0] + rad, p[1] + rad], fill=col)

    bones(FAR, PALE_GREEN, int(lw * 0.8))
    for k in ("far_elbow", "far_knee"):
        dot(k, PALE_GREEN, int(r * 0.9))
    for k in ("far_hand", "far_foot"):
        dot(k, PALE_ORANGE, int(ro * 0.9))
    bones(MID, GREEN, lw)
    bones(NEAR, GREEN, lw)
    for k in ("neck", "pelvis", "near_elbow", "near_knee"):
        dot(k, GREEN, r)
    dot("head", GREEN, int(r * 1.5))
    if ball:
        bp = (ox + ball[0] * scale, oy - ball[1] * scale); br = BALL_R * scale
        d.ellipse([bp[0] - br, bp[1] - br, bp[0] + br, bp[1] + br], fill=PURPLE)
    for k in ("near_hand", "near_foot"):
        dot(k, ORANGE, ro)
    # the hand that holds the ball is redrawn on top of it, so it is clear which hand touches the ball
    if ball:
        hk = min(("near_hand", "far_hand"), key=lambda k: math.hypot(J[k][0] - ball[0], J[k][1] - ball[1]))
        dot(hk, ORANGE if hk == "near_hand" else PALE_ORANGE, ro if hk == "near_hand" else int(ro * 0.9))
    im.save(out)
    return {"scale": scale, "points": {k: list(v) for k, v in P.items()}, "ball_px": list(bp) if ball else None}


LEGEND = ("Image 2 is a stick-figure pose rig seen from the side. Bright green lines and dots are the spine, the head and the "
          "limbs on the side of the body NEAREST the viewer. Pale green lines are the limbs on the FAR side of the body. Orange "
          "dots are the hands and feet (pale orange = far side). The PURPLE circle is the basketball: match its position relative "
          "to the body and which hand touches it exactly.")

if __name__ == "__main__":
    if sys.argv[1] == "--builtin":
        pose = POSES[sys.argv[2]](); out = sys.argv[3]
    else:
        pose = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
    size = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 1024
    info = draw(pose, out, size)
    json.dump({"pose": pose, "px": info["points"], "ball_px": info["ball_px"], "scale": info["scale"]},
              open(out.rsplit(".", 1)[0] + ".json", "w"), indent=1)
    print("wrote", out)

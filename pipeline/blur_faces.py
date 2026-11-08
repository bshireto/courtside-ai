# -*- coding: utf-8 -*-
"""Blur every face except the user's: public copies of a recap, a Top 10 or a coaching clip.

  python blur_faces.py <in.mp4> <out.mp4> [--keep-user] [--every 4] [--start s] [--end s] [--hook <file.py>] [--det-width 1280]

Frame by frame:
  1. Faces: OpenCV's YuNet (models/face_detection_yunet_2023mar.onnx) on every frame (run at --det-width, boxes scaled back).
  2. Heads: YOLO11s person boxes (OpenVINO, CPU) every --every frames; the head zone of every box (top ~16 %, dilated) is blurred
     too, so a face YuNet misses (profile, back of the head, motion blur, tiny) is still covered. Boxes are reused until the next
     detection frame, dilated for the movement in between.
  3. The user (--keep-user): on the detection frames every person crop is scored with the stored "is this the user?" training set
     (players/barak_train.npz: DINOv2 ViT-S/14 embedding + clothing colours + height, the features of user_clf.py). The best box
     with p >= 0.5 is the user: the faces inside its head zone stay sharp and its head zone is not blurred. When no box clears the
     bar everyone is blurred, so a mistake only ever hides the user, never shows a friend.
  4. --hook <file.py> defines hook(i, t, img) -> img, applied after the blur (used to rewrite the date on title and stat cards).
Blur = pixelate + Gaussian inside a soft ellipse. The audio is copied from the input (the --start/--end window of it).
"""
import argparse, importlib.util, os, subprocess, sys, time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
YUNET = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
YOLO_DIR = os.path.join(HERE, "models", "yolo11s_openvino_model")
STORE = os.path.join(HERE, "players", "barak_train.npz")


# ---------------------------------------------------------------- clothing-colour features (same as track_players.py)
def _frac(mask):
    return round(float(np.count_nonzero(mask)) / max(1, mask.size), 3)


def colour_feats(hsv, x0, y0, x1, y1):
    H, W = hsv.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    bw, bh = x1 - x0, y1 - y0
    if bw < 6 or bh < 12:
        return [0, 0, 0, 0, 0, 0]

    def reg(fx0, fy0, fx1, fy1):
        return hsv[y0 + int(bh * fy0):y0 + max(int(bh * fy0) + 1, int(bh * fy1)),
                   x0 + int(bw * fx0):x0 + max(int(bw * fx0) + 1, int(bw * fx1))]
    torso = reg(0.25, 0.18, 0.75, 0.50)
    h, s, v = torso[..., 0], torso[..., 1], torso[..., 2]
    orange = ((h <= 14) | (h >= 172)) & (s >= 110) & (v >= 110)
    lime = (h >= 24) & (h <= 45) & (s >= 90) & (v >= 100)
    arms = np.concatenate([reg(0.0, 0.18, 0.28, 0.40).reshape(-1, 3), reg(0.72, 0.18, 1.0, 0.40).reshape(-1, 3)])
    ah, as_, av = arms[:, 0], arms[:, 1], arms[:, 2]
    navy = (ah >= 100) & (ah <= 150) & (as_ >= 40) & (av >= 25) & (av <= 140)
    head = reg(0.3, 0.0, 0.7, 0.07)
    hh, hs, hv = head[..., 0], head[..., 1], head[..., 2]
    skin = ((hh <= 25) | (hh >= 170)) & (hs >= 35) & (hs <= 170) & (hv >= 90)
    dark = hv < 60
    shoe = reg(0.0, 0.93, 1.0, 1.0)
    sh, ss, sv = shoe[..., 0], shoe[..., 1], shoe[..., 2]
    red = ((sh <= 10) | (sh >= 170)) & (ss >= 100) & (sv >= 50)
    return [_frac(orange), _frac(lime), _frac(navy), _frac(skin), _frac(dark), _frac(red)]


# ---------------------------------------------------------------- the user scorer (stored training set, no new labels)
class UserScorer:
    def __init__(self):
        import torch
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        torch.set_num_threads(4)
        self.torch = torch
        local = os.path.join(os.path.expanduser("~"), ".cache", "torch", "hub", "facebookresearch_dinov2_main")
        if os.path.isdir(local):   # the cached repo: no network call (GitHub timed out mid-run once)
            self.model = torch.hub.load(local, "dinov2_vits14", source="local", trust_repo=True).eval()
        else:
            self.model = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14", trust_repo=True).eval()
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        st = np.load(STORE)
        self.clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced"))
        self.clf.fit(st["X"], st["y"])
        print("user model: %d stored crops" % len(st["y"]), flush=True)

    def score(self, img, boxes):
        torch = self.torch
        H, W = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        crops, cols, hs = [], [], []
        for (x0, y0, x1, y1) in boxes:
            w, h = x1 - x0, y1 - y0
            pad = 0.12
            cx0, cy0 = max(0, int(x0 - w * pad)), max(0, int(y0 - h * pad * 0.6))
            cx1, cy1 = min(W, int(x1 + w * pad)), min(H, int(y1 + h * pad * 0.3))
            c = cv2.resize(rgb[cy0:cy1, cx0:cx1], (98, 196), interpolation=cv2.INTER_LINEAR)
            a = torch.from_numpy(c.astype(np.float32) / 255.0).permute(2, 0, 1)
            crops.append((a - self.mean) / self.std)
            cols.append(colour_feats(hsv, x0, y0, x1, y1))
            hs.append([h / 400.0])
        with torch.no_grad():
            e = self.model(torch.stack(crops))
        e = torch.nn.functional.normalize(e, dim=1).numpy().astype(np.float32)
        X = np.hstack([e, np.array(cols, np.float32) * 2.0, np.array(hs, np.float32)])
        return self.clf.predict_proba(X)[:, 1]


# ---------------------------------------------------------------- blur
def blur_ellipse(img, cx, cy, rx, ry):
    H, W = img.shape[:2]
    rx, ry = max(6, int(rx)), max(6, int(ry))
    x0, y0, x1, y1 = max(0, int(cx - rx)), max(0, int(cy - ry)), min(W, int(cx + rx) + 1), min(H, int(cy + ry) + 1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    roi = img[y0:y1, x0:x1]
    cell = max(2, int(max(rx, ry) / 4))                                   # pixelate to ~8 cells across
    small = cv2.resize(roi, (max(1, roi.shape[1] // cell), max(1, roi.shape[0] // cell)), interpolation=cv2.INTER_AREA)
    pix = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
    k = max(5, (int(max(rx, ry) * 0.5)) | 1)
    pix = cv2.GaussianBlur(pix, (k, k), 0)
    mask = np.zeros(roi.shape[:2], np.uint8)
    cv2.ellipse(mask, (int(cx - x0), int(cy - y0)), (rx, ry), 0, 0, 360, 255, -1)
    mask = cv2.GaussianBlur(mask, (9, 9), 0)
    a = (mask[..., None].astype(np.float32) / 255.0)
    img[y0:y1, x0:x1] = (roi * (1 - a) + pix * a).astype(np.uint8)


def head_zone(box, dilate=1.0):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    return ((x0 + x1) / 2.0, y0 + 0.09 * h, max(0.30 * w, 0.075 * h) * dilate, 0.10 * h * dilate)


def inside(ellipse, px, py, scale=1.0):
    cx, cy, rx, ry = ellipse
    return ((px - cx) / (rx * scale)) ** 2 + ((py - cy) / (ry * scale)) ** 2 <= 1.0


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--keep-user", action="store_true")
    ap.add_argument("--every", type=int, default=4)
    ap.add_argument("--start", type=float, default=0.0); ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--hook", default=None)
    ap.add_argument("--det-width", type=int, default=1280)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--keep-box", action="append", default=[], help="x0,y0,x1,y1 never blurred (repeatable); e.g. the user's head when the recogniser is unsure")
    a = ap.parse_args()

    is_image = a.src.lower().endswith((".jpg", ".jpeg", ".png"))
    if is_image:
        img0 = cv2.imread(a.src)
        assert img0 is not None, a.src
        fps, W, H, n_total = 1.0, img0.shape[1], img0.shape[0], 1
        cap = None
    else:
        cap = cv2.VideoCapture(a.src)
    if cap is not None:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    f0 = int(round(a.start * fps)); f1 = int(round(a.end * fps)) if a.end else n_total
    if cap is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f0)

    dw = min(a.det_width, W); dh = int(round(H * dw / W)); sx = W / dw
    yunet = cv2.FaceDetectorYN.create(YUNET, "", (dw, dh), 0.55, 0.3, 5000)
    from ultralytics import YOLO
    yolo = YOLO(YOLO_DIR, task="detect")
    scorer = UserScorer() if a.keep_user else None

    hook = keep = None
    if a.hook:
        spec = importlib.util.spec_from_file_location("hook_mod", a.hook)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        hook = getattr(mod, "hook", None)
        keep = getattr(mod, "keep", None)      # keep(i, t) -> [(x0, y0, x1, y1), ...]: nothing inside is blurred (the user's own card photo)

    fixed_keep = [tuple(int(v) for v in kb.split(",")) for kb in a.keep_box]
    dur = (f1 - f0) / fps
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-ss", str(a.start), "-t", str(dur), "-i", a.src, "-map", "0:v", "-map", "1:a?",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-g", "60",
           "-c:a", "aac", "-b:a", "192k", "-shortest", a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE) if not is_image else None

    boxes, user_i, user_p = [], None, 0.0
    t0 = time.time(); n_faces = n_user = 0
    for i in range(f0, f1):
        if is_image:
            ok, img = True, img0.copy()
        else:
            ok, img = cap.read()
        if not ok:
            break
        t = i / fps
        if (i - f0) % a.every == 0:
            r = yolo.predict(img, imgsz=1280, conf=0.25, classes=[0], verbose=False)[0]
            bx = r.boxes.xyxy.cpu().numpy().astype(int) if r.boxes is not None else np.zeros((0, 4), int)
            boxes = [tuple(b) for b in bx if (b[3] - b[1]) >= 50]
            user_i, user_p = None, 0.0
            if scorer is not None and boxes:
                p = scorer.score(img, boxes)
                j = int(np.argmax(p))
                if p[j] >= 0.5:
                    user_i, user_p = j, float(p[j]); n_user += 1
        user_ell = head_zone(boxes[user_i], 1.6) if user_i is not None else None
        keep_rects = (keep(i, t) if keep is not None else []) + fixed_keep

        def kept(px, py):
            return any(x0 <= px <= x1 and y0 <= py <= y1 for (x0, y0, x1, y1) in keep_rects)

        small = cv2.resize(img, (dw, dh), interpolation=cv2.INTER_AREA)
        _, faces = yunet.detect(small)
        if faces is not None:
            for f in faces:
                fx, fy, fw, fh = f[0] * sx, f[1] * sx, f[2] * sx, f[3] * sx
                cx, cy = fx + fw / 2, fy + fh / 2
                if (user_ell is not None and inside(user_ell, cx, cy)) or kept(cx, cy):
                    continue
                blur_ellipse(img, cx, cy - fh * 0.05, fw * 0.85, fh * 0.95); n_faces += 1
        for k, b in enumerate(boxes):
            if k == user_i:
                continue
            cx, cy, rx, ry = head_zone(b, 1.3)
            if (user_ell is not None and inside(user_ell, cx, cy, 0.6)) or kept(cx, cy):
                continue
            blur_ellipse(img, cx, cy, rx, ry)
        if hook is not None:
            img = hook(i, t, img)
        if is_image:
            cv2.imwrite(a.out, img, [cv2.IMWRITE_JPEG_QUALITY, 92]); print("wrote", a.out, "| faces:", n_faces, "| user found:", user_i is not None); return
        enc.stdin.write(img.tobytes())
        if (i - f0) % 300 == 0:
            el = time.time() - t0
            print("frame %d/%d  t=%.1fs  faces=%d user_frames=%d  %.1f fps" % (i, f1, t, n_faces, n_user, max(1, i - f0) / max(1e-6, el)), flush=True)
    enc.stdin.close(); enc.wait()
    print("wrote", a.out, "| faces blurred:", n_faces, "| detection frames with the user:", n_user)


if __name__ == "__main__":
    main()

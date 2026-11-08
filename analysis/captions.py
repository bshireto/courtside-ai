"""Caption overlays for the coaching clips: PNGs rendered with PIL so Hebrew (right-to-left, mixed with English lingo)
comes out shaped correctly. ffmpeg's drawtext cannot do that.

  overlay_png(path, caption=..., tag=..., labels=[(x, y, text), ...], size=1920x1080)
Returns the path. Text is wrapped by measured width. Logical order in, visual order out (python-bidi).
"""
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display

W, H = 1920, 1080
BOLD = "segoeuib.ttf"
REG = "segoeui.ttf"


def font(size, bold=True):
    return ImageFont.truetype(BOLD if bold else REG, size)


def wrap(text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(get_display(t), font=fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def overlay_png(path, caption=None, tag=None, labels=(), caption_size=46, bottom=150, max_w=1680, tag_pos="right"):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if caption:
        f = font(caption_size)
        lines = wrap(caption, f, max_w)
        lh = int(caption_size * 1.32)
        tw = max(d.textlength(get_display(l), font=f) for l in lines)
        y_bottom = H - bottom + caption_size          # baseline area of the last line
        y_top = y_bottom - lh * len(lines)
        d.rectangle([W / 2 - tw / 2 - 30, y_top - 14, W / 2 + tw / 2 + 30, y_bottom + 16], fill=(0, 0, 0, 160))
        for i, l in enumerate(lines):
            vis = get_display(l)
            lw = d.textlength(vis, font=f)
            d.text((W / 2 - lw / 2, y_top + i * lh), vis, fill="white", font=f)
    if tag:
        f = font(34)
        vis = get_display(tag)
        tw = d.textlength(vis, font=f)
        tx = (W - tw) / 2 if tag_pos == "center" else W - tw - 69
        ty = 104 if tag_pos == "center" else 50
        d.rectangle([tx - 27, ty - 6, tx + tw + 27, ty + 50], fill=(0, 0, 0, 140))
        d.text((tx, ty), vis, fill="white", font=f)
    for (x, y, text) in labels:
        f = font(30)
        vis = get_display(text)
        tw = d.textlength(vis, font=f)
        d.rectangle([x - 12, y - 8, x + tw + 12, y + 44], fill=(0, 0, 0, 150))
        d.text((x, y), vis, fill="white", font=f)
    im.save(path)
    return path

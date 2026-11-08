"""10-second stats closer (1920x1080) for one player, with his photo.

  python stats_card.py stats.json out.mov
stats.json: {"name", "photo", "minutes", "date", "stats": [["FG", "2/12", "17%"], ...], "note"}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FB, FR = r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf"
s = json.load(open(sys.argv[1], encoding="utf-8"))
out = sys.argv[2]
SECS = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0   # 10 s for the reel closer; shorter when nine cards run back to back
png = out + ".png"

bg = Image.new("RGB", (1920, 1080), (14, 16, 20))
ph = Image.open(s["photo"]).convert("RGB")
ph = ph.resize((int(ph.width * 900 / ph.height), 900), Image.LANCZOS)
blur = ph.resize((1920, int(ph.height * 1920 / ph.width))).filter(ImageFilter.GaussianBlur(40))
bg.paste(Image.blend(blur.crop((0, 0, 1920, 1080)), Image.new("RGB", (1920, 1080), (0, 0, 0)), 0.7), (0, 0))
px = 170
bg.paste(ph, (px, 90))
d = ImageDraw.Draw(bg)
x0 = px + ph.width + 110
d.text((x0, 110), s["name"].upper(), font=ImageFont.truetype(FB, 104), fill=(255, 255, 255))
d.text((x0, 245), (f"{s['date']}  |  {s['minutes']} min on court" if s.get("minutes") not in (None, "") else s["date"]), font=ImageFont.truetype(FR, 40), fill=(200, 205, 212))
y = 350
for label, big, small in s["stats"]:
    d.text((x0, y), label.upper(), font=ImageFont.truetype(FB, 34), fill=(160, 166, 176))
    d.text((x0 + 360, y - 18), big, font=ImageFont.truetype(FB, 70), fill=(255, 255, 255))
    if small:
        w = d.textlength(big, font=ImageFont.truetype(FB, 70))
        d.text((x0 + 360 + w + 24, y + 4), small, font=ImageFont.truetype(FR, 40), fill=(200, 205, 212))
    y += 108
if s.get("note"):
    d.text((x0, y + 10), s["note"], font=ImageFont.truetype(FR, 28), fill=(150, 156, 166))
bg.save(png)

D = SECS
fc = (f"[0:v]fps=30,trim=end_frame={int(D * 30)},setpts=N/30/TB,"
      f"scale=w='trunc(1920*(1+0.03*t/{D})/2)*2':h='trunc(1080*(1+0.03*t/{D})/2)*2':eval=frame,"
      f"crop=1920:1080:(iw-1920)/2:(ih-1080)/2,scale=1920:1080:out_range=tv,setsar=1,fade=t=in:d=0.4,fade=t=out:st={D - 0.6}:d=0.6,format=yuv420p[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(D + 0.2), "-i", png,
                "-f", "lavfi", "-t", str(D), "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex", fc,
                "-map", "[v]", "-map", "1:a",
                # same encoder settings as render_v2.ENC, so the card can be joined to the clips without re-encoding
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-g", "60", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
                "-video_track_timescale", "15360", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-t", str(D), out], check=True)
print(out)

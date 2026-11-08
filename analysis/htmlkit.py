"""Shared pieces for the self-contained HTML deliverables (analysis report, research report).
Tokens follow ~/.claude/skills/investing-design-system/colors_and_type.css (same set the decision-map template uses).
"""
import base64, io, os, html as _html
from PIL import Image

CSS = """
:root{--grey-0:#FFFFFF;--grey-5:#FAFBFD;--grey-10:#F4F6FA;--grey-15:#EEF2F7;--grey-20:#E3E9F1;--grey-50:#D3DCE7;--grey-100:#B5C0CE;
--grey-500:#718096;--grey-700:#4A5568;--grey-800:#2D3A4E;--grey-900:#10213A;--navy:#002D62;--thunder:#007AC1;--sunset:#EF3B24;--sun:#FDBB30;
--pumpkin-orange:var(--sunset);--mandarin-orange:var(--thunder);
--blue-link:#005F99;--blue-interactive:var(--thunder);--green-positive:#007C32;--green-bg:#E6F2EC;--red-negative:#D91400;--red-bg:#FBE7E6;
--yellow-warn:var(--sun);--purple-ai:#6244FF;--stroke-weak:#E3E9F1;--stroke-medium:#D3DCE7;--text-primary:var(--grey-900);
--text-secondary:var(--grey-700);--text-tertiary:var(--grey-500);--surface-page:var(--grey-0);--surface-well:var(--grey-10);
--surface-alt:var(--grey-5);--surface-dark:var(--navy);--border-default:var(--stroke-weak);--border-strong:var(--stroke-medium);
--r-1:4px;--r-2:6px;--r-3:16px;--r-pill:9999px;--shadow-sm:0 1px 2px rgba(0,45,98,.06);
--font-sans:"Heebo","Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
--viz-1:#007AC1;--viz-2:#EF3B24;--viz-3:#002D62;--viz-4:#718096;--viz-5:#007C32;--viz-6:#FDBB30;--viz-track:#E9EEF5}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;scroll-padding-top:70px}
body{font-family:var(--font-sans);font-size:16px;line-height:1.6;color:var(--text-primary);background:var(--surface-well);-webkit-font-smoothing:antialiased}
.num,table{font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}
strong,b{font-weight:600}
a{color:var(--blue-link)}
.up{color:var(--green-positive)} .down{color:var(--red-negative)}
.topbar{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.95);backdrop-filter:saturate(180%) blur(8px);border-bottom:1px solid var(--border-default)}
.topbar-in{max-width:1100px;margin:0 auto;padding:10px 24px;display:flex;align-items:center;gap:16px}
.topbar-title{font-size:14px;font-weight:600;flex:0 0 auto;max-width:36%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.topbar nav{display:flex;gap:4px;flex-wrap:wrap;flex:1;justify-content:flex-end}
.topbar nav a{font-size:12.5px;font-weight:600;color:var(--text-secondary);text-decoration:none;padding:5px 9px;border-radius:var(--r-1)}
.topbar nav a:hover{background:var(--surface-well);color:var(--text-primary)}
.dot{width:10px;height:10px;border-radius:var(--r-pill);background:var(--sunset);box-shadow:0 0 0 3px #FDBB30 inset;display:inline-block}
.hero{background:var(--surface-page);border-bottom:1px solid var(--border-default);padding:40px 0 30px;margin-bottom:28px}
.hero-in,.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
.wrap{padding-bottom:96px}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--pumpkin-orange);margin-bottom:10px}
.hero h1{font-size:32px;font-weight:700;letter-spacing:-.015em;line-height:1.2;margin-bottom:12px}
.hero .sub{font-size:17px;line-height:1.6;color:var(--text-secondary);max-width:820px}
.hero .sub strong{color:var(--text-primary)}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
.pill{background:var(--surface-well);border:1px solid var(--border-default);border-radius:var(--r-pill);padding:4px 12px;font-size:12px;font-weight:500;color:var(--text-secondary)}
.pill strong{color:var(--text-primary);font-weight:600}
.pill.brand{background:#E6F2FA;border-color:#B9DDF3;color:#004A7A}
.card{background:var(--surface-page);border:1px solid var(--border-default);border-radius:var(--r-3);padding:28px 32px;margin-bottom:24px;box-shadow:var(--shadow-sm)}
.card h2{font-size:22px;font-weight:700;letter-spacing:-.01em;line-height:1.3;margin-bottom:6px}
.card h3{font-size:17px;font-weight:700;margin:22px 0 8px}
.card h4{font-size:15px;font-weight:700;margin:16px 0 6px}
.card p{margin-bottom:10px;color:var(--text-primary)}
.card .lead{font-size:17px;color:var(--text-secondary);margin-bottom:16px;max-width:80ch}
.card ul,.card ol{margin:6px 0 12px;padding-inline-start:22px}
.card li{margin-bottom:5px}
.label{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--text-tertiary);margin:18px 0 10px}
.tldr{background:var(--surface-dark);color:#fff;border-radius:var(--r-3);padding:24px 28px;margin-bottom:28px}
.tldr h2{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--sun);margin-bottom:14px}
.tldr p{color:#fff;font-size:17px;line-height:1.55;margin-bottom:10px}
.tldr .muted{color:#C9D6E5;font-size:14px}
.tldr-row{display:grid;grid-template-columns:28px 1fr;gap:14px;padding:10px 0;border-top:1px solid rgba(255,255,255,.1);align-items:start}
.tldr-row:first-of-type{border-top:0}
.tldr-n{width:24px;height:24px;border-radius:var(--r-pill);background:var(--sunset);color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}
.tldr-q{font-size:15px;font-weight:600;color:#fff;line-height:1.45}
.tldr-q small{display:block;font-weight:400;color:#C9D6E5;font-size:13.5px;margin-top:2px}
.stats{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));margin:12px 0 18px}
.stat{border:1px solid var(--border-default);border-radius:var(--r-2);padding:14px 16px;background:var(--surface-page)}
.stat-label{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-tertiary);margin-bottom:6px}
.stat-value{font-size:28px;font-weight:700;line-height:1.1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat-sub{font-size:12.5px;color:var(--text-secondary);margin-top:5px}
.stat.pos .stat-value{color:var(--green-positive)} .stat.neg .stat-value{color:var(--red-negative)}
.stat.accent{border-color:#B9DDF3;background:#F1F8FD}
table.t{width:100%;border-collapse:separate;border-spacing:0;font-size:14px;margin:8px 0 16px}
table.t th,table.t td{border-bottom:1px solid var(--border-default);padding:9px 10px;text-align:start;vertical-align:top}
table.t th{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-tertiary);border-bottom:1px solid var(--border-strong)}
table.t td.c{text-align:center}
.good{background:var(--green-bg);color:var(--green-positive);font-weight:600}
.mid{background:var(--surface-well);color:var(--text-secondary)}
.bad{background:var(--red-bg);color:var(--red-negative)}
.tag{display:inline-block;font-size:11.5px;font-weight:600;border-radius:var(--r-pill);padding:2px 9px;background:var(--surface-well);border:1px solid var(--border-default);color:var(--text-secondary);margin:2px 4px 2px 0}
.tag.pos{background:var(--green-bg);border-color:#C3DED0;color:var(--green-positive)}
.tag.neg{background:var(--red-bg);border-color:#F3C9C6;color:var(--red-negative)}
.tag.warn{background:#FFF4D6;border-color:#FDDC8A;color:#5A3E00}
.badge{background:var(--green-positive);color:#fff;font-size:11px;font-weight:700;letter-spacing:.03em;padding:2px 9px;border-radius:var(--r-pill);text-transform:uppercase}
.badge.grey{background:var(--grey-500)} .badge.red{background:var(--red-negative)} .badge.orange{background:var(--pumpkin-orange)}
.bars{display:flex;flex-direction:column;gap:9px;margin:10px 0 16px}
.bar-row{display:grid;grid-template-columns:minmax(120px,240px) 1fr auto;gap:12px;align-items:center;font-size:13.5px}
.bar-name{color:var(--text-secondary);text-align:end}
.bar-track{background:var(--viz-track);border-radius:var(--r-1);height:18px;position:relative;overflow:hidden}
.bar{height:100%;border-radius:var(--r-1);background:var(--viz-1);min-width:3px}
.bar.pos{background:var(--green-positive)} .bar.neg{background:var(--red-negative)} .bar.c2{background:var(--viz-2)} .bar.c4{background:var(--viz-4)}
.bar-val{font-weight:600;font-size:13px;white-space:nowrap;min-width:44px}
.fix{border:1px solid var(--border-default);border-radius:var(--r-2);padding:18px 20px;margin-bottom:14px;background:var(--surface-page);display:grid;grid-template-columns:44px 1fr;gap:16px}
.fix-n{width:40px;height:40px;border-radius:var(--r-1);background:var(--thunder);color:#fff;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700}
.fix h3{margin:0 0 6px;font-size:18px}
.fix .cue{display:inline-block;background:#FFF4D6;border:1px solid #FDDC8A;color:#5A3E00;border-radius:var(--r-1);padding:6px 12px;font-weight:600;margin:8px 0}
.fix .why{color:var(--text-secondary);font-size:15px}
.frames{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));margin:12px 0 18px}
.frame-card{border:1px solid var(--border-default);border-radius:var(--r-2);overflow:hidden;background:var(--surface-page)}
.frame-card img{display:block;width:100%;height:auto}
.frame-cap{padding:9px 12px;font-size:13.5px;line-height:1.45}
.frame-cap b{display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-tertiary);margin-bottom:3px}
.frame-card.pos .frame-cap b{color:var(--green-positive)} .frame-card.neg .frame-cap b{color:var(--red-negative)}
.vids{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));margin:12px 0 16px}
.vid{margin:0}
.vid video{display:block;width:100%;height:auto;border-radius:var(--r-2);background:#000}
.vid figcaption{font-size:13.5px;color:var(--text-secondary);margin-top:6px;line-height:1.4}
.viz{border:1px solid var(--border-default);border-radius:var(--r-2);padding:18px;margin:12px 0 18px;background:var(--surface-page);overflow-x:auto}
.viz img{display:block;width:100%;height:auto;border-radius:var(--r-1)}
.viz-cap{font-size:13px;color:var(--text-tertiary);margin-top:12px;line-height:1.5}
.viz-title{font-size:14px;font-weight:600;margin-bottom:12px}
details.more{border:1px solid var(--border-default);border-radius:var(--r-1);margin:10px 0 16px;background:var(--surface-alt)}
details.more>summary{cursor:pointer;padding:10px 14px;font-size:14px;font-weight:600;color:var(--text-secondary);list-style:none}
details.more>summary::-webkit-details-marker{display:none}
details.more>summary::before{content:"+ ";color:var(--pumpkin-orange);font-weight:700}
details.more[open]>summary::before{content:"\\2013  "}
details.more .more-body{padding:0 14px 14px;font-size:14.5px;line-height:1.6;color:var(--text-secondary)}
.two{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.callout{border-inline-start:3px solid var(--thunder);background:var(--surface-well);border-radius:var(--r-1);padding:12px 16px;margin:10px 0 16px;font-size:15.5px}
.callout.green{border-color:var(--green-positive)} .callout.red{border-color:var(--red-negative)}
.verdict{font-size:12px;font-weight:700;border-radius:var(--r-pill);padding:2px 8px;text-transform:uppercase;letter-spacing:.04em}
.verdict.confirmed{background:var(--green-bg);color:var(--green-positive)} .verdict.partly{background:#FFF4D6;color:#5A3E00}
.verdict.refuted{background:var(--red-bg);color:var(--red-negative)} .verdict.not_visible{background:var(--surface-well);color:var(--text-secondary)}
.md h1{font-size:26px;margin:10px 0 14px} .md h2{font-size:22px;margin:28px 0 10px;padding-top:8px;border-top:1px solid var(--border-default)}
.md h3{font-size:17px;margin:20px 0 8px} .md p{margin-bottom:10px} .md ul,.md ol{margin:6px 0 12px;padding-inline-start:22px} .md li{margin-bottom:5px}
.md table{width:100%;border-collapse:separate;border-spacing:0;font-size:14px;margin:8px 0 16px}
.md th,.md td{border-bottom:1px solid var(--border-default);padding:8px 10px;text-align:start;vertical-align:top}
.md th{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text-tertiary)}
.md code{font-family:Consolas,"SF Mono",monospace;font-size:13px;background:var(--surface-well);padding:1px 5px;border-radius:3px}
.md blockquote{border-inline-start:3px solid var(--grey-50);padding:4px 14px;color:var(--text-secondary);margin:8px 0 12px}
.foot{font-size:13px;color:var(--text-tertiary);margin-top:30px}
@media (max-width:720px){.hero h1{font-size:25px}.card{padding:20px 18px}.fix{grid-template-columns:1fr}.bar-row{grid-template-columns:minmax(80px,120px) 1fr auto}}
@media print{.topbar{display:none}body{background:#fff}.card{break-inside:avoid;box-shadow:none}details.more{display:block}details.more>.more-body{display:block}}
"""

WORDMARK = '<span class="dot"></span>'


def esc(s):
    return _html.escape("" if s is None else str(s), quote=False)


def img_b64(path, max_w=960, quality=78, crop=None):
    """Return a data: URI for an image, resized to max_w (and optionally cropped first: (x0,y0,x1,y1))."""
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def page(title, eyebrow, h1, sub, pills, body, nav=None, lang="en", dir="ltr"):
    navhtml = "".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in (nav or []))
    pillhtml = "".join(f'<span class="pill{(" brand" if b else "")}">{p}</span>' for p, b in pills)
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{dir}"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>@import url("https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap");{CSS}</style></head>
<body>
<div class="topbar"><div class="topbar-in">{WORDMARK}<div class="topbar-title">{esc(title)}</div><nav>{navhtml}</nav></div></div>
<header class="hero"><div class="hero-in"><div class="eyebrow">{esc(eyebrow)}</div><h1>{esc(h1)}</h1><p class="sub">{sub}</p><div class="pills">{pillhtml}</div></div></header>
<div class="wrap">
{body}
</div></body></html>"""


def md_to_html(md_text):
    import markdown
    return markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists", "toc"])

"""Assemble results/research.md from results/research_sections/*.md and generate section 10 (Sources) from the links used."""
import glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.join(HERE, "results", "research_sections")
TITLES = {1: "What the research says in one page", 2: "How to break down one player's offense reel", 3: "Feedback that changes behaviour",
          4: "Drill library mapped to weakness types", 5: "Output formats, compared", 6: "What a single wide camera can and cannot measure",
          7: "Benchmarks and the maths of shot selection", 8: "Rebuilding the jump shot as an adult", 9: "Interesting extras"}
parts, sources, missing = [], [], []
pre = os.path.join(SEC, "00_preamble.md")
if os.path.exists(pre):
    parts.append(open(pre, encoding="utf-8").read().strip())
for n in range(1, 10):
    p = os.path.join(SEC, f"{n:02d}.md")
    if not os.path.exists(p):
        missing.append(n); continue
    md = open(p, encoding="utf-8").read().strip()
    # normalise the heading
    md = re.sub(r"^#+\s*\d*\.?\s*.*?\n", f"## {n}. {TITLES[n]}\n", md, count=1) if not md.startswith(f"## {n}.") else md
    parts.append(md)
    seen = set()
    links = []
    for text, url in re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", md):
        if url not in seen:
            seen.add(url); links.append((text.strip(), url))
    sources.append((n, links))
src = ["## 10. Sources"]
for n, links in sources:
    src.append(f"\n**{n}. {TITLES[n]}**\n")
    for text, url in links:
        src.append(f"- [{text}]({url})")
parts.append("\n".join(src))
out = "\n\n".join(parts) + "\n"
open(os.path.join(HERE, "results", "research.md"), "w", encoding="utf-8", newline="\n").write(out)
print("research.md:", len(out.split()), "words;", sum(len(l) for _, l in sources), "source links; missing sections:", missing or "none")

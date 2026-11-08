"""Generate workflows/research_sections.js: one small agent per report section (2-9), each writing its own file.
Reuses the CONTEXT constant of research_resume2.js. Section 1 keeps the synthesizer's draft; section 10 (Sources) is
assembled by assemble_research.py from the links in the other sections.
"""
import re, sys
A = "<project>/analysis_2026-10-07"
src = open("workflows/research_resume2.js", encoding="utf-8").read()
m = re.search(r"const CONTEXT = `.*?`\n", src, re.S)
assert m, "CONTEXT not found"
context = m.group(0)
todo = [int(x) for x in sys.argv[1:]] or [2, 3, 4, 5, 6, 7, 8, 9]

SECTIONS = {
    2: ("How to break down one player's offense reel", [1, 2, 6], False,
        "a concrete per-possession tagging scheme (fields and allowed values) and the per-game roll-ups (tendencies, shot mix, shot quality, decision quality), adapted to what a wide camera can see. Include the recommended order of a film session / report (what goes first, positive-to-corrective ratio, one priority at a time)."),
    3: ("Feedback that changes behaviour", [2, 4, 7], False,
        "cue design (external focus, short cues), frequency, summary vs immediate, self-modelling / feedforward clips, transfer to game shots, with the evidence and effect sizes where the sources give them."),
    4: ("Drill library mapped to weakness types", [3, 7, 2, 6], False,
        "a table: weakness -> 2-3 drills with reps/sets, cue, progress test, source. Cover: shot selection/decision, pull-up balance, guide hand / elbow / one motion, finishing with contact and off hand, triple threat and first step, catch-and-shoot and relocation, passing out of the drive, rebounding, conditioning for adult legs. Then a 25-minute solo session template with make counts."),
    5: ("Output formats, compared", [4, 1, 2, 5], True,
        "a table of every delivery format found (HTML report, captioned coaching video, annotated clip playlist, side-by-side with a model/pro, pose-skeleton overlay, shot chart / hex map, tendency report, progress tracker across games, voice-over review, short cue card, etc.): what it is, what it takes to produce with ffmpeg/Python/HTML, what evidence or expert opinion says about its effect on behaviour, and a verdict (build first / later / skip) for this situation."),
    6: ("What a single wide camera can and cannot measure", [5, 4], False,
        "the measure-automatically / judge-by-eye / needs-close-up split, with the pose-estimation subject-size evidence, and a concrete camera add-on recommendation for form (height, angle, distance, fps)."),
    7: ("Benchmarks and the maths of shot selection", [6, 1], False,
        "expected points per shot by zone and by defender distance / dribbles, what 13 shots can and cannot tell you (intervals), what to track per game and across games."),
    8: ("Rebuilding the jump shot as an adult", [7, 3, 2], False,
        "consensus and the counter-arguments, protocol with make counts, timeline expectations, how to keep it under game pressure."),
    9: ("Interesting extras", [1, 2, 3, 4, 5, 6, 7], True,
        "8-12 ideas nobody asked for that would genuinely help, drawn from the researchers' 'interesting' lists and the gap-fill findings, each one line with a source."),
}
KEYS = {1: "1_film-frameworks", 2: "2_feedback-science", 3: "3_drills-mapping", 4: "4_output-formats", 5: "5_cv-feasibility", 6: "6_benchmarks-shot-quality", 7: "7_form-rebuild-transfer"}


def repr_sections(S, todo):
    items = []
    for n in todo:
        title, files, crit, covers = S[n]
        fl = ", ".join(f"'{A}/results/partial/sweep/{KEYS[i]}.json'" for i in files)
        items.append(f"  {{ n: {n}, title: {title!r}, files: [{fl}], critique: {str(crit).lower()}, file: '{n:02d}.md', covers: {covers!r} }}")
    return "[\n" + ",\n".join(items) + "\n]"


body = f"""export const meta = {{
  name: 'bball-research-sections',
  description: 'Write the remaining sections of the research report, one small agent per section, each saving its own Markdown file',
  phases: [ {{ title: 'Sections', detail: 'one writer per section' }} ],
}}

{context}
const RES = '{A}/results'
const SECTIONS = {repr_sections(SECTIONS, todo)}

phase('Sections')
const out = await parallel(SECTIONS.map(s => () =>
  agent(`${{CONTEXT}}

You are writing ONE SECTION of a ten-section research report for Barak; other agents write the other sections, so write only yours, starting with the exact heading "## ${{s.n}}. ${{s.title}}" and nothing before it. The section covers: ${{s.covers}}

INPUT FILES (Read every one in full before writing; use offset/limit if a read is cut short):
Research sweeps for this section (findings with source URLs, output_format_ideas, drills, interesting, gaps):
${{s.files.join('\\n')}}
Fact-check verdicts on the 44 load-bearing claims (index, verdict, claim, corrected_claim, source_url):
${{RES}}/research_verdicts_compact.json
${{s.critique ? 'Gap-fill findings from the completeness critic (angle "Gap-fill", mark these GF):\\n' + RES + '/research_critique.json' : ''}}

Rules:
- Where a verdict says refuted, drop or correct the claim. Where partly, state the corrected version. Where unverifiable, keep only if useful and mark it "(unverified)". Findings not covered by a verdict are fine to use; do not invent sources.
- Every substantive statement carries its source URL in Markdown link form, using URLs that appear in the input files.
- Plain, direct language. Short sentences. No hype. No emoji. Numbers go in tables where possible. Aim for 350-700 words (section 4 may run to 900 with its table).
WHEN DONE: write the section Markdown to ${{RES}}/research_sections/${{s.file}} with the Write tool, then return the same Markdown as your final text.`,
    {{ label: `section:${{s.n}}`, phase: 'Sections' }})))
return {{ written: out.filter(Boolean).length, sections: SECTIONS.map(s => s.n) }}
"""


body = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", body).replace("\r\n", "\n")
open("workflows/research_sections.js", "w", encoding="utf-8", newline="\n").write(body)
print("wrote workflows/research_sections.js", len(body), "sections", todo)

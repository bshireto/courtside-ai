export const meta = {
  name: 'bball-research-sections',
  description: 'Write the remaining sections of the research report, one small agent per section, each saving its own Markdown file',
  phases: [ { title: 'Sections', detail: 'one writer per section' } ],
}

const CONTEXT = `
SITUATION (read carefully, it shapes what is useful):
- The player ("Barak") is an adult recreational basketball player. He plays pickup 4-on-4 half-court games at night on a covered outdoor court, roughly weekly. Not a pro, not a youth player.
- Footage: ONE fixed phone camera on the near sideline around mid-court, wide lens, 1920x1080 at 30 fps. Players are only ~100-160 px tall in frame. The hoop is seen from the side. Fine hand mechanics are hard to read; gross mechanics (jump, balance, landing, one- vs two-hand release, arc, footwork, decisions, spacing, shot selection) are readable.
- He already has a working Python/ffmpeg pipeline (YOLO11 detections, player tracking, make/miss detection at the rim, shooter attribution, per-player stats cards, an "offense reel" of all his possessions, Top 10 videos). The offense reel for the last game is 5:16 long: 27 clips, each one of his offensive possessions, with "+2 PTS / ASSIST" pop-ups and a stats card.
- Last game line: 12 points, 5/13 FG (38%), 2/5 threes, 3/8 twos, 2 assists, ~28 minutes over 3 games. Many of his shots are pull-up jumpers after a long hold / size-up at the top of the arc against the same defender; several contested; two airballs; he also had good rebounds and loose-ball recoveries and lob/drop-off passes.
- A separate close-up shooting-form analysis in July 2026 (front, low angle, one rep) found: strong leg load and balance (good), but a two-hand push release, shooting elbow flaring out, ball carried dead-centre in front of the face, and a two-motion (dip, pause, push) rhythm. Drills were prescribed (one-hand form shooting, silent guide hand, wall snaps, one-motion rhythm).
- Tooling available for the analysis workflow: Claude (vision over extracted frames and contact sheets, NOT native video viewing), ffmpeg 8.1, Python with OpenCV, ultralytics YOLO11 (detection and pose models), torch CPU, Pillow, matplotlib; ability to render annotated videos (captions, overlays, slow-motion, zoom, side-by-side) with ffmpeg; ability to produce self-contained HTML reports.
- GOAL: design a recurring workflow where, after every game, the reel is analysed and he gets insights, drills and anything that takes his game to the next level; and decide which output formats (HTML report, captioned video, annotated clips, shot chart, pose overlays, progress tracker, etc.) are worth building.

RESEARCH RULES:
- Use WebSearch (mode "extended" when a standard search is thin) and WebFetch to read the actual pages. Do not answer from memory alone; every finding carries a URL you actually opened.
- Prefer primary and expert sources: coaching organisations, peer-reviewed sports-science papers, established player-development coaches, product documentation (Hudl, Synergy, HomeCourt, Noah, Dartfish, OnForm), NBA tracking-data analyses, well-known basketball analytics writers.
- Be concrete: names of frameworks, taxonomies, numbers, cue words, drill names with reps, product features. Vague statements ("video analysis is helpful") are worthless.
- Mark a finding load_bearing=true only if the final recommendations would change if it were false (about 3-6 per researcher).
- Return raw structured data via the StructuredOutput tool. Your final text is data, not a message to a human.
`

const RES = '<project>/analysis_2026-10-07/results'
const SECTIONS = [
  { n: 3, title: 'Feedback that changes behaviour', files: ['<project>/analysis_2026-10-07/results/partial/sweep/2_feedback-science.json', '<project>/analysis_2026-10-07/results/partial/sweep/4_output-formats.json', '<project>/analysis_2026-10-07/results/partial/sweep/7_form-rebuild-transfer.json'], critique: false, file: '03.md', covers: 'cue design (external focus, short cues), frequency, summary vs immediate, self-modelling / feedforward clips, transfer to game shots, with the evidence and effect sizes where the sources give them.' },
  { n: 4, title: 'Drill library mapped to weakness types', files: ['<project>/analysis_2026-10-07/results/partial/sweep/3_drills-mapping.json', '<project>/analysis_2026-10-07/results/partial/sweep/7_form-rebuild-transfer.json', '<project>/analysis_2026-10-07/results/partial/sweep/2_feedback-science.json', '<project>/analysis_2026-10-07/results/partial/sweep/6_benchmarks-shot-quality.json'], critique: false, file: '04.md', covers: 'a table: weakness -> 2-3 drills with reps/sets, cue, progress test, source. Cover: shot selection/decision, pull-up balance, guide hand / elbow / one motion, finishing with contact and off hand, triple threat and first step, catch-and-shoot and relocation, passing out of the drive, rebounding, conditioning for adult legs. Then a 25-minute solo session template with make counts.' },
  { n: 5, title: 'Output formats, compared', files: ['<project>/analysis_2026-10-07/results/partial/sweep/4_output-formats.json', '<project>/analysis_2026-10-07/results/partial/sweep/1_film-frameworks.json', '<project>/analysis_2026-10-07/results/partial/sweep/2_feedback-science.json', '<project>/analysis_2026-10-07/results/partial/sweep/5_cv-feasibility.json'], critique: true, file: '05.md', covers: 'a table of every delivery format found (HTML report, captioned coaching video, annotated clip playlist, side-by-side with a model/pro, pose-skeleton overlay, shot chart / hex map, tendency report, progress tracker across games, voice-over review, short cue card, etc.): what it is, what it takes to produce with ffmpeg/Python/HTML, what evidence or expert opinion says about its effect on behaviour, and a verdict (build first / later / skip) for this situation.' },
  { n: 6, title: 'What a single wide camera can and cannot measure', files: ['<project>/analysis_2026-10-07/results/partial/sweep/5_cv-feasibility.json', '<project>/analysis_2026-10-07/results/partial/sweep/4_output-formats.json'], critique: false, file: '06.md', covers: 'the measure-automatically / judge-by-eye / needs-close-up split, with the pose-estimation subject-size evidence, and a concrete camera add-on recommendation for form (height, angle, distance, fps).' },
  { n: 7, title: 'Benchmarks and the maths of shot selection', files: ['<project>/analysis_2026-10-07/results/partial/sweep/6_benchmarks-shot-quality.json', '<project>/analysis_2026-10-07/results/partial/sweep/1_film-frameworks.json'], critique: false, file: '07.md', covers: 'expected points per shot by zone and by defender distance / dribbles, what 13 shots can and cannot tell you (intervals), what to track per game and across games.' },
  { n: 8, title: 'Rebuilding the jump shot as an adult', files: ['<project>/analysis_2026-10-07/results/partial/sweep/7_form-rebuild-transfer.json', '<project>/analysis_2026-10-07/results/partial/sweep/3_drills-mapping.json', '<project>/analysis_2026-10-07/results/partial/sweep/2_feedback-science.json'], critique: false, file: '08.md', covers: 'consensus and the counter-arguments, protocol with make counts, timeline expectations, how to keep it under game pressure.' },
  { n: 9, title: 'Interesting extras', files: ['<project>/analysis_2026-10-07/results/partial/sweep/1_film-frameworks.json', '<project>/analysis_2026-10-07/results/partial/sweep/2_feedback-science.json', '<project>/analysis_2026-10-07/results/partial/sweep/3_drills-mapping.json', '<project>/analysis_2026-10-07/results/partial/sweep/4_output-formats.json', '<project>/analysis_2026-10-07/results/partial/sweep/5_cv-feasibility.json', '<project>/analysis_2026-10-07/results/partial/sweep/6_benchmarks-shot-quality.json', '<project>/analysis_2026-10-07/results/partial/sweep/7_form-rebuild-transfer.json'], critique: true, file: '09.md', covers: "8-12 ideas nobody asked for that would genuinely help, drawn from the researchers' 'interesting' lists and the gap-fill findings, each one line with a source." }
]

phase('Sections')
const out = await parallel(SECTIONS.map(s => () =>
  agent(`${CONTEXT}

You are writing ONE SECTION of a ten-section research report for Barak; other agents write the other sections, so write only yours, starting with the exact heading "## ${s.n}. ${s.title}" and nothing before it. The section covers: ${s.covers}

INPUT FILES (Read every one in full before writing; use offset/limit if a read is cut short):
Research sweeps for this section (findings with source URLs, output_format_ideas, drills, interesting, gaps):
${s.files.join('\n')}
Fact-check verdicts on the 44 load-bearing claims (index, verdict, claim, corrected_claim, source_url):
${RES}/research_verdicts_compact.json
${s.critique ? 'Gap-fill findings from the completeness critic (angle "Gap-fill", mark these GF):\n' + RES + '/research_critique.json' : ''}

Rules:
- Where a verdict says refuted, drop or correct the claim. Where partly, state the corrected version. Where unverifiable, keep only if useful and mark it "(unverified)". Findings not covered by a verdict are fine to use; do not invent sources.
- Every substantive statement carries its source URL in Markdown link form, using URLs that appear in the input files.
- Plain, direct language. Short sentences. No hype. No emoji. Numbers go in tables where possible. Aim for 350-700 words (section 4 may run to 900 with its table).
WHEN DONE: write the section Markdown to ${RES}/research_sections/${s.file} with the Write tool, then return the same Markdown as your final text.`,
    { label: `section:${s.n}`, phase: 'Sections' })))
return { written: out.filter(Boolean).length, sections: SECTIONS.map(s => s.n) }

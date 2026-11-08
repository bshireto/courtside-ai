"""Derive the v2 resume scripts (agents read the saved results from disk) from the v1 resume scripts."""
import re
A = "<project>/analysis_2026-10-07"


def rep(src, old, new, count=1):
    assert src.count(old) == count, (old[:60], src.count(old))
    return src.replace(old, new)


# ---------------- clip analysis ----------------
s = open("workflows/clip_analysis_resume.js", encoding="utf-8").read()
s = rep(s, "name: 'bball-reel-clip-analysis-resume',", "name: 'bball-reel-clip-analysis-resume2',")
s = rep(s, "description: 'Analyse all 27 possessions of Barak offense reel from contact sheets, synthesize through three coaching lenses, aggregate a scouting report, adversarially verify every claim',",
        "description: 'Resume: synthesize the 27 saved possession records through three coaching lenses, aggregate a scouting report, adversarially verify every claim against the frames',")
s = rep(s, "    { title: 'Clips', detail: 'one vision agent per possession (27)' },\n", "")
start = s.index("phase('Clips')")
end = s.index("const GAME_CONTEXT")
head = """const RES = '__A__/results'
const RECORD_FILES = [1, 2, 3].map(n => `${RES}/records_part${n}.json`)
const READ_RECORDS = `THE 27 PER-POSSESSION RECORDS are on disk in three JSON files (clips 0-8, 9-17, 18-26). Read ALL THREE in full with the Read tool before doing anything else (each is ~700 lines; use offset/limit if a read is cut short, and do not stop until you have seen clip 26):
${RECORD_FILES.join('\\n')}
Each record follows one fixed schema: clip, narrative, play_start, on_ball_sequence, hold_seconds_before_action, dribbles_before_release_or_pass, drive_direction, dribble_hand, defender, shot{...}, pass{...}, rebound_or_loose_ball{...}, off_ball_before_touch, spacing_and_open_teammates, better_option_available, decision_quality, decision_reason, execution_quality, execution_reason, positives, improvement_cue, teaching_frames[], visibility_limits, confidence.`
log('Resuming from 27 saved records on disk')

""".replace("__A__", A)
s = s[:start] + head + s[end:]
s = rep(s, "PER-POSSESSION RECORDS (JSON):\n${JSON.stringify(recs)}`", "${READ_RECORDS}`")
s = rep(s, "PER-POSSESSION RECORDS:\n${JSON.stringify(recs)}`", "${READ_RECORDS}`")
s = rep(s, "return { records: recs, lenses: lensOk, report, verdicts: vOk }",
        "return { lenses: lensOk.length, headline: report?.headline, claims: claims.length, verdicts: vOk.length, tally }")
leftover = [m.start() for m in re.finditer(r"\brecs\b", s)]
assert not leftover, leftover
open("workflows/clip_analysis_resume2.js", "w", encoding="utf-8").write(s)
print("clip_analysis_resume2.js", len(s))

# ---------------- research ----------------
r = open("workflows/research_resume.js", encoding="utf-8").read()
r = rep(r, "name: 'bball-offense-analysis-research-resume',", "name: 'bball-offense-analysis-research-resume2',")
r = rep(r, "    { title: 'Sweep', detail: 'seven researchers, each a different angle' },\n    { title: 'Verify', detail: 'independent skeptic per load-bearing claim' },\n",
        "    { title: 'Verify', detail: 'the 16 load-bearing claims the first run did not get to' },\n")
start = r.index("const sweepOk = ")
tail = open("workflows/_research_tail.js.txt", encoding="utf-8").read().replace("__A__", A)
r = r[:start] + tail
open("workflows/research_resume2.js", "w", encoding="utf-8").write(r)
print("research_resume2.js", len(r))

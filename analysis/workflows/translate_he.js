export const meta = {
  name: 'bball-review-translate-he',
  description: 'Translate the remaining English parts of the offense review into plain Hebrew: the skeptic corrections and the 27 possession-log narratives with their cues',
  phases: [ { title: 'Translate', detail: 'verdicts + three blocks of possessions' } ],
}
const A = '<project>/analysis_2026-10-07'
const RULES = `
LANGUAGE: plain, natural Hebrew addressed to Barak in the masculine second person. English only for accepted lingo (floater, pull-up, layup, closeout, crossover, hesitation, jab step), explained in plain Hebrew the first time it appears in a text. Names: ברק, המגן, המגן, המגן, המגן, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה. Numbers, times (0:42.6), clip numbers and shot ids (c007, s011) exactly as in the source. Keep every fact: nothing added, nothing dropped, same direction of every claim. No coaching jargon left unexplained: "sag" -> "עומד רחוק ממך", "check" -> "הצ'ק (החזרת הכדור למעלה אחרי סל)", "closeout" -> "המגן רץ אליך לסגור", "pull-up" -> "זריקה ישר אחרי כדרור", "gather" -> "איסוף הכדור לזריקה", "outlet" -> "המסירה הראשונה אחרי ריבאונד", "paint" -> "הצבע (המלבן מתחת לסל)", "elbow" -> "פינת קו העונשין", "top of the key / arc" -> "ראש הקשת (מול הסל, על קו השלוש)".
Return ONLY a JSON object as your final text (no code fences).`

phase('Translate')
const jobs = [
  { key: 'verdicts', prompt: `${RULES}
TASK: Read ${A}/results/verdicts.json (24 skeptic verdicts on the report's claims; fields claim, verdict, evidence, corrected_claim, clips_checked). Return {"verdicts": [{"claim": <original claim verbatim>, "evidence_he": <Hebrew translation of evidence, at most 120 words, keep every number and clip reference>, "corrected_claim_he": <Hebrew translation of corrected_claim, full>}, ...]} in the same order.` },
  ...[[0, 8], [9, 17], [18, 26]].map(([a, b]) => ({ key: `log:${a}-${b}`, prompt: `${RULES}
TASK: Read ${A}/results/records_part${a === 0 ? 1 : a === 9 ? 2 : 3}.json (possession records, clips ${a}-${b}). For each record return its clip number, the "narrative" translated into plain Hebrew (full, every time and name kept), the "improvement_cue" in Hebrew (at most 12 words), and "play_start" in Hebrew (e.g. defensive_rebound -> ריבאונד הגנה, check_ball -> צ'ק למעלה, offensive_rebound -> ריבאונד התקפה, loose_ball -> כדור חופשי, outlet_catch -> קבלת מסירה אחרי ריבאונד, handoff -> מסירת יד ליד, cut_catch -> חיתוך וקבלה, spot_up_catch -> קבלה בעמידה, inbound -> הכנסה, other -> אחר). Return {"records": [{"clip": n, "play_start_he": "...", "narrative_he": "...", "cue_he": "..."}, ...]} for clips ${a}-${b}.` })),
]
const out = await parallel(jobs.map(j => () => agent(j.prompt, { label: `translate:${j.key}`, phase: 'Translate' })))
const parse = s => { try { return JSON.parse(String(s).trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '')) } catch (e) { return null } }
const parsed = out.map(parse)
return { verdicts: parsed[0]?.verdicts?.length || 0, records: parsed.slice(1).reduce((n, p) => n + (p?.records?.length || 0), 0) }

export const meta = {
  name: 'bball-drive-analysis',
  description: 'For every drive in the offense reel: which side was open from the defender stance, which side and angle he took, hesitation before the drive; patterns; skeptic check. Hebrew output.',
  phases: [
    { title: 'Drives', detail: 'one reviewer per drive possession (13)' },
    { title: 'Patterns', detail: 'counts across the drives, priorities, cues' },
    { title: 'Verify', detail: 'skeptic re-watches the frames behind each pattern' },
    { title: 'Finalize', detail: 'head coach rewrites the summary from the corrected claims' },
  ],
}

const A = '<project>/analysis_2026-10-07'
const BRIEFS = `${A}/briefs`
const FRAMES = `${A}/work/frames`
const COURT = `
HOW TO READ THE FOOTAGE
- One fixed phone camera on the near sideline around mid-court, looking right toward the hoop. The hoop (rim ~ (1254,320) in full-frame px) is at the top right, seen from the side; the white backboard is right of the rim. Night, covered outdoor court.
- A big dark out-of-focus object covers the TOP-LEFT of the frame; players behind it are hidden (only legs/arms may show).
- Court lines: the big WHITE arc is the 3-point line; its apex (farthest from the hoop) is at the left ~ (527,645) px full-frame. The red-brown rectangle is the paint; the free-throw line is its LEFT edge. YELLOW lines belong to another sport: ignore them. Half-court game: both teams attack this one hoop; after a make or defensive rebound the ball is taken back out past the arc and "checked" (bounced to the defender and back) at the top.
- Times: every tile is stamped "reel m:ss.s" (time inside the offense reel) and "src m:ss.s" (time in the original game video). Use REEL time when you cite a moment.
- Sheet kinds: "flow" = wide court crop, 2 frames per second, 2 columns x 4 rows, read left-to-right then down. "zoom" = a 640x560 window that follows Barak's tracked box at 5 fps ([box] = tracker had him, [xy] = window placed on the shot position, [fallback] = tracker lost him, the window may NOT contain him). "shot strip" = the same window at 10 fps from 1.4 s before the release to 1.0 s after it, the tile marked RELEASE is the release frame. "release frame" = the full 1920x1080 frame at the release (judge the feet against the arc here).

WHO IS WHO
- BARAK (the player we analyse): bald / shaved light-skinned head, medium-heavy build, dark-red / maroon short-sleeve T-shirt, black knee-length shorts with a white side stripe, black socks, maroon / red sneakers. Game 1 (G1): no pinnie. Games 2-3 (G2, G3): an ORANGE pinnie over the maroon shirt (red sleeves show).
- Look-alikes who are NOT him: the defender (bald, black T-shirt, dark shoes; lime pinnie rolled around the neck from G2), the defender (bald, heavier, all black with LONG trousers), a teammate (short grey hair, grey T-shirt, beige shorts).
- His usual defender: the defender - wavy grey-brown hair, black sleeveless top, black shorts, bright ORANGE shoes (lime pinnie from G2).
- Other opponents: the defender (dark hair + beard, white sleeveless top; lime from G2), the defender, the defender.
- Teammates: a teammate (tall, dark hair + beard, black tank top, dark green shorts), a teammate (white T-shirt, white shorts; G1 and G3), a teammate (grey T-shirt, beige shorts; G1 and G2), a teammate (dark hair + beard, BLUE shorts, white shoes; G2 and G3).
`

const HEBREW = `
LANGUAGE: all free-text fields in natural, plain Hebrew addressed to Barak in the masculine second person ("אתה", "ימין שלך"). English only for accepted lingo (floater, pull-up, layup, closeout, crossover, hesitation / "hezi", jab step), explained in plain Hebrew the first time. Names: ברק, המגן, המגן, המגן, המגן, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה. Numbers as digits. "Right" and "left" ALWAYS from Barak's own point of view, written explicitly ("ימין שלך", "שמאל שלך"); when you describe the defender's hand or foot say whose it is ("יד שמאל של המגן").
`
const ITEMS = [
 {
  "clip": 2,
  "reel_start": 26.9,
  "reel_end": 40.57,
  "narrative": "Check-ball possession from the top in G1: Barak takes the check from the defender at reel 28.9 (upper body hidden behind the foreground object), holds and organises for about two seconds, then spends roughly five seconds dribbling against a set the defender: a right-hand probe toward his right side, a pull-back, and a re-set at the top with a teammate hovering a step away inside the arc and four other bodies standing in the paint. At reel 35.7-36.1 he finally attacks right-handed and beats the defender cleanly, defender trailing on his hip into the free-throw line. The defender, the defender and the defender are waiting at the top of the paint, so he picks the ball up in the crowd (36.3) and drops it to a teammate near the rim (ball reaches a teammate at 37.3; the release itself is occluded). A teammate's contested layup misses at 38.1 but he grabs his own rebound and goes back up at 39.4-39.9. Right final read, slow setup: the drive worked, but it came late into a paint nobody had cleared.",
  "sequence": [
   "catch",
   "hold",
   "dribble_right",
   "pull_back",
   "dribble",
   "drive_right",
   "gather",
   "pass"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender (black sleeveless top, orange shoes) - tight on him from the check, beaten on the drive at 35.9; the defender, the defender and the defender as help defenders at the free-throw line / top of the paint",
  "better_option": "none clearly better - the drop-off to a teammate was the right read; a teammate alone at the top of the key inside the arc at reel 36.4 was only a reset / long two",
  "question": ""
 },
 {
  "clip": 8,
  "reel_start": 86.43,
  "reel_end": 99.13,
  "narrative": "a teammate's miss came off the rim, the defender bobbled the rebound, and Barak read it first, scooping the loose ball a step inside the free-throw line at 1:28.4 with the defender already on him. Rather than attack a scrambled defense, he dribbled out to the top of the key on the far side (briefly hidden behind the defender at 1:30.4-1:30.9), then turned and drove down the far/left side of the lane to the far elbow with the defender on his hip and the defender and the defender waiting inside. He gathered at 1:33.7, went up off one foot and dropped a very high-arc runner over the defender's raised hand at 1:34.3; the ball fell through at ~1:35.6 (reel overlay shows BARAK 4 PTS). Well-executed, but a tougher shot than the possession needed: a teammate stood unguarded at the top of the key and a teammate beyond the arc on the left wing for the whole drive, and a simple kick-out was there from 1:32.4 on.",
  "sequence": [
   "loose_ball_scoop",
   "dribble_out_to_top_far_side",
   "dribble_behind_Yaron",
   "chest_high_hesitation_dribble",
   "drive_left_to_far_elbow",
   "gather",
   "one_foot_runner",
   "shot_made"
  ],
  "drive_direction": "left",
  "dribble_hand": "right",
  "defender": "the defender (black sleeveless, orange shoes) on him from the scoop to the release; the defender and the defender as help standing in the lane",
  "better_option": "Kick-out to a teammate, wide open at the top of the key at reel 1:33.4 (a teammate beyond the arc on the left wing was also open at 1:33.4)",
  "question": ""
 },
 {
  "clip": 9,
  "reel_start": 99.13,
  "reel_end": 108.3,
  "narrative": "Barak catches the check at the top of the key at 1:41.1, holds about a second in triple threat with a shot fake at 1:41.8, then attacks right-handed straight at the defender from 1:42.2. The defender backpedals and gets bumped onto a teammate, who is standing at the top of the free-throw circle (1:43.4), but Barak bends to his left around the pair with the ball still in his right (inside) hand, so the defender slides with him and is on his hip at the far elbow. He picks the ball up around 1:44.8, holds it at the chest for roughly 0.3 s, and rises off a low jump into a 16-foot pull-up at 1:45.6 with the defender's hand at the ball and five players standing in the lane. The arc is high and the ball rims out straight up (1:47.1); he lands balanced but stays at the elbow and the defense rebounds (1:48.1).",
  "sequence": [
   "catch",
   "hold",
   "shot_fake",
   "dribble_right",
   "drive_left",
   "pick_up",
   "gather",
   "shot"
  ],
  "drive_direction": "left",
  "dribble_hand": "right",
  "defender": "the defender (black sleeveless top, orange shoes) - in his stance from the check, retreats in front of him, bumped onto a teammate at 1:43.4 but stays on his hip and has a hand at the ball at the release (1:45.4-1:45.7).",
  "better_option": "none seen (no open teammate at any point). Ball-handling alternative: after the bump at 1:43.4 keep the dribble - turn the corner into the lane with the left hand or pull it back out and reset the spacing - instead of rising at the elbow with the defender attached (1:45.6).",
  "question": ""
 },
 {
  "clip": 10,
  "reel_start": 108.3,
  "reel_end": 119.57,
  "narrative": "Barak sprints from the right block to the top to take a dribble handoff from a teammate with the defender trailing him by two steps (1:48.8-1:49.8); the handoff itself and his dribble out to the left (1:50.3-1:53.1) are hidden behind the dark object, but the defender's orange shoes stay parked at the far-left frame edge through 1:52.8, so the ball went away from the rim long enough for the defence to reset. He re-emerges at 1:53.3 driving toward the rim with the defender back on his hip, the defender steps up off a teammate at 1:53.5, and Barak picks up his dribble at 1:53.7 at the top of the key (roughly 18 feet out) with two defenders on him, pivots to protect the ball, and kicks it back over the defender's raised arms to the open a teammate at 1:54.3 (caught 1:54.7). The read was right (when the screener's man helps, the screener is the pass), but the drive went into a lane already holding a teammate, a teammate and two defenders, and the ball died well outside the paint, so the pass had to come from a dead dribble. A teammate drives from 1:55.5 and the play stops around 1:57.8 with no shot reaching the rim.",
  "sequence": [
   "sprint_to_handoff (right block to top-left, 1:48.8-1:50.3)",
   "handoff_catch (hidden, ~1:50.3)",
   "dribble_out_left_away_from_rim (hidden, ~1:50.6-1:51.3 per pipeline)",
   "crossover_turn_back (hidden, ~1:52.1-1:52.6 per pipeline)",
   "drive_right_toward_rim (visible 1:53.3-1:53.7, the defender on hip, the defender stepping up)",
   "pick_up_dribble (1:53.7, top of the key)",
   "pivot_under_two_defenders (1:53.7-1:54.1)",
   "kick_back_pass_to_Yehuda (release 1:54.3, caught 1:54.7)"
  ],
  "drive_direction": "right",
  "dribble_hand": "unclear",
  "defender": "the defender (black sleeveless, orange shoes) on the ball the whole way, re-attached to his hip by 1:53.3; the defender (white sleeveless) leaves a teammate and steps up at 1:53.5 to form a two-man squeeze at the top of the key through the pass at 1:54.3.",
  "better_option": "Same target, earlier: a teammate at the top-left was open from 1:53.5 (reel 113.5 s) when the defender stepped up; a live-dribble kick-back then, before the dribble died at 1:53.7, beats the dead-dribble pass at 1:54.3. One step further back, the handoff itself was the advantage (the defender two steps behind at 1:49.8); attacking downhill on the catch instead of dribbling out to the left would have hit the lane before the defender was set. Nobody else was open: a teammate and a teammate were in the paint with the defender and the defender on them.",
  "question": ""
 },
 {
  "clip": 11,
  "reel_start": 119.57,
  "reel_end": 133.4,
  "narrative": "Barak jogs out from the lane to take a teammate's outlet past the arc at the top-left (catch 2:01.5) and squares up with the defender sagging about 2 m off him. He sits in a low triple-threat for about 2.2 s without moving the defender, then drives left-handed toward the near-side elbow at 2:03.7; the defender closes on the first dribble and stays on his hoop-side hip, so after about three dribbles Barak picks the ball up at the free-throw line (2:05.1) with five bodies in front of him and no pass ready. He protects the ball, pivots away from the defender and keeps it high while a teammate lifts from the baseline past him, then flips a hand-off at 2:06.5. A teammate dribbles out to the top and knocks down a jumper (release 2:08.1, through at about 2:09.8), so the possession ends in an assist. Sound ball security and a good bail-out read, but the drive itself never created an advantage because the hold let the defense set.",
  "sequence": [
   "catch",
   "hold",
   "drive_left",
   "pick_up",
   "pivot",
   "handoff"
  ],
  "drive_direction": "left",
  "dribble_hand": "left",
  "defender": "the defender (black sleeveless top, orange shoes) - on him from the catch through the hand-off; the defender was also near the top at the catch but drifted to a teammate",
  "better_option": "An in-rhythm pull-up 3 at the arc apex at 2:03.1 (the defender sagging ~2 m off) or an immediate attack on the catch at 2:01.6 before the defender got set; no teammate was open - a teammate, a teammate and a teammate were all guarded inside the arc.",
  "question": ""
 },
 {
  "clip": 13,
  "reel_start": 143.8,
  "reel_end": 157.2,
  "narrative": "After the check at 2:25.8 Barak held the ball overhead for about 1.4 s against the defender's pressure, then took roughly four right-hand dribbles toward the hoop while the defender sagged two metres off him at the top of the arc, and at 2:30.0 lobbed over the defender's jump to a teammate cutting down the near side of the lane - a risky pass, but completed. A teammate's drive stalled, the ball went out to a teammate at the far elbow, and Barak cut into a handoff at 2:33.5 with the defender screened off; after one dribble (0.1 s hold off the catch) he picked the ball up at the free-throw line with the defender set a metre in front of him. He dropped the ball to his waist, raised it and released a two-hand overhead push at 2:34.7 straight into the defender's raised hand: the ball went almost straight up, fell a metre in front of him and a teammate collected the loose ball. The step he gained off the handoff was the moment to attack the rim; once he killed the dribble, a teammate was open at the top of the key for the kick-out.",
  "sequence": [
   "check_catch (2:25.8)",
   "hold_overhead vs the defender (2:25.8-2:27.2)",
   "dribble_right x4 approx, the defender sagging (2:27.2-2:29.4)",
   "pick_up (2:29.6)",
   "lob_pass to a teammate over the defender's jump (2:30.0)",
   "stand top-left outside the arc (2:30.6-2:32.6)",
   "cut into a teammate's handoff (2:33.0-2:33.5)",
   "handoff_catch (2:33.5)",
   "dribble_right x1 (2:33.6-2:33.8)",
   "gather (2:34.0)",
   "hold_pivot, ball dropped to the waist (2:34.0-2:34.5)",
   "two_hand_set_shot, release 2:34.7, contested by the defender",
   "airball drops in the lane (2:34.8-2:35.5), not secured"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender on the ball from the check (sagged ~2 m while Barak dribbled at the top, jumped at the lob, screened off on the handoff); the defender stepped up from the lane and contested the shot with his hand at the ball; the defender right behind the defender.",
  "better_option": "Keep the dribble off the handoff and attack the defender's hip at 2:33.7 (reel 153.7) - the defender was screened off; after the pickup, a teammate open at the top-left of the free-throw circle at 2:34.5 (reel 154.5)",
  "question": ""
 },
 {
  "clip": 14,
  "reel_start": 157.2,
  "reel_end": 166.0,
  "narrative": "After the defender checks the ball to him at the top of the key (in his hands at 2:39.2), Barak holds for about half a second and then dribbles in place for roughly 1.7 s while the defender sits in a stance in front of him and the defender and the defender settle into the paint behind. He drives right from 2:41.7, but the defender never leaves his hip, and by the time he crosses the free-throw line (2:42.7) two helpers are already waiting. He gathers in the paint with the ball at chest height at 2:43.0 and goes up through three bodies; the defender contests with a hand up, the defender reaches in from the right, the ball hits the rim and falls out, and the defender takes the rebound at 2:45.7. A teammate stood alone at the top of the arc from 2:42.7 through the release, so the kick-out was there the whole time.",
  "sequence": [
   "catch",
   "hold",
   "dribble_in_place",
   "drive_right",
   "gather",
   "shot",
   "miss"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender (lime pinnie, orange shoes) from the catch to the rim, attached to his hip the whole drive and contesting with a hand up at the release; the defender (all black, long trousers) reaching in from the right and the defender (lime, bald) on the left at the finish.",
  "better_option": "Kick-out to a teammate at the top of the arc, alone from reel 2:42.7 to 2:43.5; or a jump-stop at the free-throw line at 2:42.7 for a short shot before the defender and the defender closed.",
  "question": ""
 },
 {
  "clip": 15,
  "reel_start": 166.0,
  "reel_end": 174.4,
  "narrative": "Check-ball possession at the top of the arc: Barak takes the bounce-back from the defender at 2:48.0, holds for about 0.8 s and puts the ball on the floor with his right hand at 2:48.8. For the next 3.2 s he pound-dribbles in place with his back bent nearly flat and his eyes on the ball (clearest 2:49.6-2:51.0), mixes in two crossovers, drifts back to the outer edge of the arc, and never moves the defender, who stays square in front with his hands at his sides. The last two dribbles are left-hand, straight into the defender's right hip; he then picks the ball up and hands it off to a teammate arriving from the far side of the key at ~2:52.0 - the exchange is clean but the defense simply switches and a teammate restarts at the apex. The whole time a teammate stood alone at the near low block (nearest defender the defender across the lane) and the entire near side of the floor was empty - an early entry pass or a right-hand attack to that side was the play.",
  "sequence": [
   "check_to_defender",
   "catch",
   "hold",
   "dribble_right",
   "crossover_to_left",
   "crossover_to_right",
   "dribble_right",
   "retreat",
   "crossover_to_left",
   "drive_left",
   "pick_up",
   "handoff"
  ],
  "drive_direction": "left",
  "dribble_hand": "both",
  "defender": "the defender (lime pinnie, orange shoes) - square in front the whole possession, hands at his sides, never pressured the ball",
  "better_option": "a teammate, alone at the near low block at reel 2:49.0-2:50.5 (the defender across the lane, the defender's hands down) - an early entry pass, or a right-hand drive to the empty near side with a teammate as the drop-off.",
  "question": ""
 },
 {
  "clip": 20,
  "reel_start": 217.9,
  "reel_end": 236.0,
  "narrative": "a teammate's drive misses and Barak crashes from the left side of the lane, securing the offensive rebound with two hands above his head about seven feet from the rim at 3:39.9 with the defender beside him. Instead of going back up or chinning the ball, he brings it straight down to his waist and flips it softly to his left at 3:40.3; nobody is ready for it (a teammate never moves his hands), the ball bounces at 3:40.9 and Barak has to chase it down himself at 3:41.3. He dribbles out to the left wing where the defender picks him up and pounds the dribble for roughly four seconds (3:43.0-3:46.8), while a teammate and a teammate stand in a paint that already holds the defender, the defender and the defender and a teammate is alone at the top of the arc. At 3:46.8 he drives right into that crowd, picks the ball up with two hands at 3:48.0, gets wrapped up by the defender, puts the ball on the floor again, and bails out at 3:49.2 with a low drop-off that bounces at a teammate's feet; a teammate collects it at ~3:49.8 and the possession continues. The team keeps the ball, but two touches with the ball created no advantage and twice came close to a turnover.",
  "sequence": [
   "offensive_rebound (two hands, high, 3:39.9)",
   "bring_ball_down_to_waist",
   "soft_flip_pass_left_to_nobody (3:40.3)",
   "loose_ball (3:40.9)",
   "recover_own_loose_ball (3:41.3)",
   "dribble_left_out_to_wing (3:41.6-3:43.0)",
   "dribble_hold_on_left_wing_vs_Yonatan (3:43.0-3:46.8, partly hidden)",
   "drive_right_into_lane (3:46.8-3:47.4)",
   "gather_two_hands (3:48.0)",
   "re_dribble_or_fumble_under_Yaron_grab (3:48.4-3:48.8)",
   "drop_off_pass_to_Yehuda (3:49.2)"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender (lime, white sleeveless) beside him on the rebound; the defender (lime pinnie, orange shoes) picks him up on the left wing from ~3:42.4 and shadows the drive; the defender (all black, long trousers) grabs and wraps him in the lane 3:48.2-3:49.0.",
  "better_option": "Two. (1) 3:39.9: go straight back up with the rebound - ball already secured high, about seven feet from the rim, only the defender beside him. (2) 3:44.9: swing to a teammate, unguarded at the top of the arc (open from 3:44.4 to ~3:46.0) instead of pounding the dribble and then driving into five bodies.",
  "question": ""
 },
 {
  "clip": 23,
  "reel_start": 261.19,
  "reel_end": 271.16,
  "narrative": "After a teammate's missed three and an orange offensive rebound under the rim, Barak relocated beyond the top of the arc, put his hands up for the kick-out (4:22.2) and caught a bounce pass from the paint (a teammate by body position) at 4:23.2 with the defender still 3-4 m away. He held about one second, then attacked right off the catch as the defender closed, beat him with a straight-line right-hand drive, kept the dribble through the defender's reach-in around 4:25.7 and got into the lane. He gathered at 4:26.1 and released a right-hand runner at 4:26.5 over the defender's raised hand; the ball peaked barely above rim height, caught the iron, sat for about half a second and dropped (make, 2 points). Good read and a strong drive; the finish was flat and needed a friendly roll.",
  "sequence": [
   "catch",
   "hold",
   "drive_right",
   "gather",
   "runner_right_hand",
   "shot_made"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender (closing out from inside, beaten off the catch at 4:24.2-4:24.7, trails the drive); the defender (all black) reaches into him at the free-throw-line area around 4:25.6-4:25.8; the defender (lime) steps up and contests the release with a raised hand at 4:26.4-4:26.5.",
  "better_option": "none seen (an open catch-and-shoot three at the top of the arc at about 4:23.5 was available with the defender 3 m away, but the paint runner he got is the higher-value shot)",
  "question": "Barak's own question about this drive (reel 4:24): 'after the shot fake (hesitation) the defender raised his right arm to try to block; it seems my angle was too wide. Or was I supposed to eventually drive right to avoid the three defenders in the lane?' Answer it explicitly in better_choice: was the angle too wide, which side was open given the defender's raised RIGHT arm, and whether going right (away from the three defenders) was the better line."
 },
 {
  "clip": 24,
  "reel_start": 271.16,
  "reel_end": 286.16,
  "narrative": "the defender checks the ball to Barak at the top of the arc (reel 4:33.2); he takes one casual right-hand dribble, then holds for about 1.8 s with a two-hand overhead fake (4:34.6-4:35.2) that moves nobody. He dribbles right off a teammate's ball screen at 4:36.2, but comes off it loosely with daylight between him and the screener and no change of pace, so the defender slides over the top and rides his hoop-side hip for the entire drive (4:36.8-4:38.0). The drive aims at the near elbow where a teammate is already standing with his defender, so Barak picks up his dribble at 4:38.2 and hands off to a teammate at 4:38.4-4:38.6. A teammate drives left into three lime bodies and loses the handle (scramble 4:41.7-4:42.7); orange recovers and a teammate gets a shot at the rim around 4:43.7. Meanwhile a teammate popped to the top after his screen and stood unguarded from 4:37.2 to 4:38.2 and never got the ball.",
  "sequence": [
   "catch",
   "dribble_right",
   "hold",
   "overhead_fake",
   "dribble_right",
   "use_screen_right",
   "drive_right",
   "pick_up",
   "handoff"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender (lime pinnie, black sleeveless top, orange shoes). He fought over a teammate's screen and stayed attached on Barak's hoop-side hip through the whole drive; a second lime defender (bald, likely the defender) was waiting on a teammate at the elbow, with the defender sagging in the paint.",
  "better_option": "a teammate - open at the top of the arc after popping from his screen, reel ~4:37.4 (visible unguarded 4:37.2-4:38.2); a pass back for an open look or a top-of-the-key drive beats handing off into the crowd at the elbow.",
  "question": ""
 },
 {
  "clip": 25,
  "reel_start": 286.16,
  "reel_end": 299.26,
  "narrative": "Barak took the defender's check-return at the top (reel 4:48.2) and held for about four seconds while a teammate stood on the near-side low block with his hand up calling for an entry pass (4:48.7-4:51.2); he never used it. He then put the ball down and backed the defender slowly toward the key, but a teammate, a teammate and a teammate all drifted in to him, so by 4:55.2 six players were inside a three-metre circle at the top of the key with nobody spaced on a wing or corner. He picked up the dribble with the defender on his hip and pushed the ball up overhead; it rose almost vertically to about rim height with no travel toward the hoop (4:56.7 to 4:57.2) and dropped onto a teammate, who was standing beside him, caught it, drove and laid it in after the clip ends. The team scored, but the process was a long hold, a drive into his own teammates and a smothered attempt; the basket was a teammate's recovery, not the play's design.",
  "sequence": [
   "catch",
   "hold",
   "dribble",
   "back_down_into_crowd",
   "gather",
   "contested_shot"
  ],
  "drive_direction": "unclear",
  "dribble_hand": "unclear",
  "defender": "the defender (lime pinnie, orange shoes) from the check to the release, draped on his hip during the back-down; the defender joined the cluster at the key from about 4:55.2.",
  "better_option": "a teammate - near-side low block, arm raised, reel 4:48.7 to 4:51.2 (288.7-291.2 s): an entry pass while he had position and his defender was sagging under the rim.",
  "question": ""
 },
 {
  "clip": 26,
  "reel_start": 299.26,
  "reel_end": 306.46,
  "narrative": "After the defender's miss and a teammate's defensive rebound, Barak had already jogged out to the far-side arc and took the head-high outlet there (reel 5:01.3), held it about 0.7 s in a deep crouch, then attacked to his right with three right-hand dribbles toward the middle. The defender backpedaled 2-3 m toward the lane as the dribble started (5:02.3) and then set himself at the far end of the free-throw line; Barak dribbled straight into him, gathered on a 1-2 stop with the defender's chest on his and every other player (a teammate, the defender, a teammate, the defender, a teammate, the defender) already inside the paint. He rose for a pull-up two from the FT line with the defender's right arm fully extended in his face, released cleanly one-handed off the top of a low jump, and the ball came up short off the front rim (5:04.9); a lime player collected the rebound while Barak stood at the line. The decision, not the form, is the issue: the space to shoot existed one dribble earlier, and the lane he drove into had no room and no open teammate.",
  "sequence": [
   "catch (head-high outlet from a teammate at the far-side arc, lands in a deep crouch)",
   "hold ~0.7 s",
   "drive_right x3 (right-hand dribbles to the middle, ball trailing at hip height)",
   "gather (two hands, into the defender's chest)",
   "1-2 stop at the far end of the FT line",
   "shot (pull-up 2, tight contest)",
   "miss short off the front rim",
   "stands at the line, no crash"
  ],
  "drive_direction": "right",
  "dribble_hand": "right",
  "defender": "the defender (lime pinnie over black sleeveless, black shorts, orange shoes). Within 1 m at the catch (5:01.8), backpedaled 2-3 m toward the lane as the dribble started (5:02.3), set at the far end of the FT line by 5:02.8, absorbed the gather on his chest and contested the release with his right arm fully extended (5:03.9). The defender (all black, long trousers) and a teammate were the next bodies 1-2 m behind him.",
  "better_option": "An open one-dribble pull-up from the far wing at reel 5:02.3-5:02.8, when the defender had backed off 2-3 m toward the lane; no teammate was open at any point (a teammate, a teammate and a teammate were all inside the paint with the four lime defenders)",
  "question": ""
 }
]

const DRIVE = {
  type: 'object',
  properties: {
    clip: { type: 'integer' },
    drive_start_reel: { type: 'number', description: 'reel time (s, one decimal) of the first drive dribble' },
    decision_reel: { type: 'number', description: 'reel time of the moment the decision is made: the last frame before the first drive dribble (or before the hesitation move that replaced the drive)' },
    passby_reel: { type: 'number', description: 'reel time when he is level with the first defender, or when the drive dies' },
    start_spot: { type: 'string' },
    defender: { type: 'string' },
    defender_at_decision: { type: 'object', properties: {
      distance_m: { type: 'number' },
      feet: { type: 'string', enum: ['square', 'left_foot_forward', 'right_foot_forward', 'unclear'], description: 'the DEFENDER\'s feet' },
      hand_up: { type: 'string', enum: ['none', 'left', 'right', 'both', 'unclear'], description: 'the DEFENDER\'s raised hand(s)' },
      weight: { type: 'string', enum: ['flat', 'back_on_heels', 'forward', 'moving_toward', 'moving_away', 'unclear'] },
      feet_px: { type: 'array', items: { type: 'number' }, description: '[x, y] full-frame pixels of the defender feet at the decision moment' },
      note: { type: 'string' },
    }, required: ['distance_m', 'feet', 'hand_up', 'weight', 'feet_px', 'note'] },
    barak_feet_px: { type: 'array', items: { type: 'number' }, description: '[x, y] full-frame pixels of Barak feet at the decision moment' },
    side_attacked: { type: 'string', enum: ['right', 'left', 'middle', 'none'], description: 'from Barak\'s point of view' },
    open_by_defender: { type: 'string', enum: ['right', 'left', 'either', 'none', 'unclear'], description: 'the side the FIRST defender\'s body gave (lead foot / raised hand / momentum), from Barak\'s point of view' },
    help_side: { type: 'string', enum: ['right', 'left', 'both', 'none', 'unclear'], description: 'the side(s) where a help defender stood in the driving path, from Barak\'s point of view' },
    help_note: { type: 'string', description: 'who the help defenders were and where they stood' },
    side_open: { type: 'string', enum: ['right', 'left', 'either', 'none', 'unclear'], description: 'the best side with both reads together, from Barak\'s point of view' },
    side_reason: { type: 'string', description: 'why that side was open: his hand, his front foot, his weight, the help defender; or why neither' },
    angle: { type: 'string', enum: ['tight_past_hip', 'wide_loop', 'lateral', 'into_chest', 'none', 'unclear'] },
    angle_note: { type: 'string', description: 'estimate of the sideways gap in metres between the two of them at the pass-by, and where the path went' },
    hesitation_moves: { type: 'integer', description: 'number of moves in place before the drive: jab, crossover in place, pound dribble, pull-back, shot fake' },
    hesitation_note: { type: 'string', description: 'what the moves were and whether any of them moved the defender' },
    first_step: { type: 'string', enum: ['explosive', 'normal', 'slow', 'none', 'unclear'] },
    pace_change: { type: 'boolean' },
    outcome: { type: 'string', enum: ['beat_defender', 'contained', 'help_stopped', 'pass', 'shot', 'turnover', 'other'] },
    outcome_note: { type: 'string' },
    right_decision: { type: 'string', enum: ['yes', 'partly', 'no', 'unclear'] },
    better_choice: { type: 'string', description: '1-2 sentences, concrete: which side, which angle, at what moment' },
    cue: { type: 'string', description: 'at most 12 Hebrew words, something to say to himself' },
    teaching_frame: { type: 'object', properties: { reel_time: { type: 'number' }, caption: { type: 'string' }, kind: { type: 'string', enum: ['positive', 'corrective'] } }, required: ['reel_time', 'caption', 'kind'] },
    visibility: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['clip', 'drive_start_reel', 'decision_reel', 'passby_reel', 'start_spot', 'defender', 'defender_at_decision', 'barak_feet_px', 'side_attacked', 'open_by_defender', 'help_side', 'help_note', 'side_open', 'side_reason', 'angle', 'angle_note', 'hesitation_moves', 'hesitation_note', 'first_step', 'pace_change', 'outcome', 'outcome_note', 'right_decision', 'better_choice', 'cue', 'teaching_frame', 'visibility', 'confidence'],
}

const pad = i => String(i).padStart(3, '0')
phase('Drives')
const drives = await parallel(ITEMS.map(it => () =>
  agent(`You are a basketball player-development coach reviewing ONE drive (a dribble attack toward the basket) by an adult recreational player, frame by frame, to answer three questions he asked: did he attack the open side (reading the defender's raised hand, front foot and weight), was the angle past the defender tight or too wide, and did a hesitation move replace the drive.

CONTEXT FOR THIS POSSESSION (written by an earlier reviewer; reliable on what happened and when, not on the drive reads):
clip ${it.clip}, reel ${it.reel_start.toFixed(1)}-${it.reel_end.toFixed(1)} s. Sequence: ${JSON.stringify(it.sequence)}. Earlier read: drive ${it.drive_direction}, dribble hand ${it.dribble_hand}. Defender: ${it.defender}
Narrative: ${it.narrative}
Better option noted earlier: ${it.better_option}
${it.question ? 'PLAYER QUESTION: ' + it.question : ''}

STEP 1: Read ${BRIEFS}/r${pad(it.clip)}.json (Read tool) and view its flow and zoom sheets (Read renders images) to find the drive.
STEP 2: View FULL-RESOLUTION FRAMES around the decision: the frame for reel time t is ${FRAMES}/<k>.jpg with k = round(t*10)+1 padded to 5 digits (e.g. t = 42.6 -> 00427.jpg). View these frames and no more than 8 images in total: 0.5 s before the first drive dribble, the decision moment, the first step, the pass-by moment (when he is level with the defender or the drive dies), and the outcome. Zoom mentally on the DEFENDER: which foot is forward, which hand is up, where his weight is, how far he stands.
STEP 3: Fill the record. SIDES IN THIS CAMERA VIEW: Barak attacks toward the right of the image. When he faces the rim from the top of the arc, his RIGHT side is the NEAR side (toward the camera, lower in the image) and his LEFT side is the FAR side (away from the camera, higher in the image). A defender facing him is mirrored: the DEFENDER's right hand and right foot are on the FAR side (Barak's left), the defender's left hand and left foot are on the NEAR side (Barak's right). Work out each hand and foot from the body, then translate to Barak's point of view. HOW TO JUDGE THE OPEN SIDE, two separate reads. Read 1, the first defender's body (field open_by_defender): (a) LEAD FOOT: the side of the foot he has forward is the side to attack, because he has to turn his hips (drop-step) before he can follow; (b) RAISED HAND: a hand raised to contest a shot or a shot fake lifts his weight and normally goes with the same-side foot forward, so the side of the RAISED hand is the open side, and his LOW hand is the one that can poke the dribble, so the low-hand side is the risky side; (c) MOMENTUM: a defender running at him or leaning one way cannot change direction, so the side against his momentum is open. Say which of a/b/c you actually saw. Read 2, the help (field help_side): where the second and third defenders stand. A side with a defender waiting in the driving path is closed even if the first defender gives it. Then side_open is the best side with BOTH reads taken together; when they conflict (his body gives one side, the help closes it) say so in side_reason and say which one mattered more on this play. Angle: tight_past_hip = shoulder goes past the defender's hip within about half a metre; wide_loop = he swings a metre or more sideways before going forward; lateral = east-west dribbling that never turns toward the basket; into_chest = straight into a set defender. Count the hesitation moves in place before the drive (jab, crossover in place, pound dribble, pull-back, shot fake) and say whether any of them moved the defender. If the drive is hidden by the dark object or by bodies, say so in visibility and lower confidence; never invent what you cannot see. Pixel positions: full-frame 1920x1080 coordinates of the feet (bottom of the body).
${HEBREW}
${COURT}`, { label: `drive:r${pad(it.clip)}`, phase: 'Drives', schema: DRIVE })))
const ok = drives.filter(Boolean)
log(`Drives done: ${ok.length}/${ITEMS.length}`)

phase('Patterns')
const PATTERNS = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: '2-4 sentences, Hebrew' },
    counts: { type: 'object', properties: {
      drives: { type: 'integer' }, open_side_taken: { type: 'integer' }, open_side_missed: { type: 'integer' }, side_unclear: { type: 'integer' },
      tight: { type: 'integer' }, wide: { type: 'integer' }, lateral: { type: 'integer' }, into_chest: { type: 'integer' },
      with_hesitation: { type: 'integer' }, hesitation_that_moved_defender: { type: 'integer' }, beat_defender: { type: 'integer' }, right_hand: { type: 'integer' }, left_hand: { type: 'integer' },
    }, required: ['drives', 'open_side_taken', 'open_side_missed', 'side_unclear', 'tight', 'wide', 'lateral', 'into_chest', 'with_hesitation', 'hesitation_that_moved_defender', 'beat_defender', 'right_hand', 'left_hand'] },
    findings: { type: 'array', items: { type: 'object', properties: {
      finding: { type: 'string' }, numbers: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } }, confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    }, required: ['finding', 'numbers', 'evidence_clips', 'confidence'] } },
    rule_check: { type: 'string', description: 'Hebrew: the raised-hand rule stated clearly with the mirror explained, then where it applied in his drives, where the help overrode it, with clip evidence' },
    priorities: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, why: { type: 'string' }, cue: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['what', 'why', 'cue', 'evidence_clips'] } },
  },
  required: ['summary', 'counts', 'findings', 'rule_check', 'priorities'],
}
const patterns = await agent(`You are the head coach summarising the drive records below (one per drive possession, written in Hebrew by frame-by-frame reviewers) for the player himself. Count: open side taken vs missed (use side_open, the read with the help included), angle types, hesitation moves and whether they moved the defender, drives that beat the first defender, dribble hand. Write 4-7 findings with counts and clip evidence, check the rule he was told. In his words: "if a defender raises his left hand to contest the shot I can drive left". The standard coaching version is: attack the side of the hand the defender raises (and of his front foot), and remember the mirror, the defender's left hand is on Barak's RIGHT. State the rule clearly in rule_check with the mirror explained, then say on which drives it applied, on which the help defenders overrode it, and how often he followed it, and give 2-3 priorities with a cue each. Where records disagree or are low confidence, say so and lower confidence.
${HEBREW}
DRIVE RECORDS:
${JSON.stringify(ok)}`, { label: 'drive-patterns', phase: 'Patterns', schema: PATTERNS })

phase('Verify')
const VERDICT = {
  type: 'object',
  properties: { claim: { type: 'string' }, verdict: { type: 'string', enum: ['confirmed', 'partly', 'refuted', 'not_visible'] }, evidence: { type: 'string' }, corrected_claim: { type: 'string' }, clips_checked: { type: 'array', items: { type: 'integer' } } },
  required: ['claim', 'verdict', 'evidence', 'clips_checked'],
}
const claims = [...(patterns?.findings || []).slice(0, 5).map(f => ({ text: `${f.finding} (${f.numbers})`, clips: f.evidence_clips })), ...(patterns?.priorities || []).slice(0, 2).map(p => ({ text: `PRIORITY: ${p.what} - ${p.why}`, clips: p.evidence_clips }))]
const verdicts = await parallel(claims.map((c, i) => () => {
  const list = (c.clips || []).slice(0, 4).map(k => `${BRIEFS}/r${pad(k)}.json`).join('\n')
  return agent(`You are a skeptical second coach. Try to REFUTE the claim below by looking at the frames: read each brief listed (Read tool), view its flow and zoom sheets, and open full-resolution frames (${FRAMES}/<k>.jpg, k = round(reel_t*10)+1, 5 digits) around the drives. Judge only what you can see: confirmed / partly (write the corrected claim) / refuted / not_visible. Right and left are from Barak's point of view. Write evidence and corrected_claim in Hebrew.
CLAIM: ${c.text}
CLIPS: ${JSON.stringify(c.clips)}
BRIEFS:
${list}
${COURT}`, { label: `verify:${i}`, phase: 'Verify', schema: VERDICT })
}))
const vOk = verdicts.filter(Boolean)
const tally = vOk.reduce((m, v) => ({ ...m, [v.verdict]: (m[v.verdict] || 0) + 1 }), {})
log(`Verify done: ${JSON.stringify(tally)}`)
phase('Finalize')
const INT = { type: 'integer' }
const CLIPS = { type: 'array', items: { type: 'integer' } }
const CHECK = { type: 'string', enum: ['confirmed', 'corrected', 'not_checked'] }
const FINAL = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: '3-5 sentences, Hebrew, every number matching the corrected findings' },
    counts: { type: 'object', properties: {
      drives: INT, open_side_taken: INT, open_side_missed: INT, side_unclear: INT, tight: INT, wide: INT, lateral: INT, into_chest: INT,
      with_hesitation: INT, hesitation_that_moved_defender: INT, beat_defender: INT, beat_defender_half_step: INT, right_hand: INT, left_hand: INT,
    }, required: ['drives', 'open_side_taken', 'open_side_missed', 'side_unclear', 'tight', 'wide', 'lateral', 'into_chest', 'with_hesitation', 'hesitation_that_moved_defender', 'beat_defender', 'beat_defender_half_step', 'right_hand', 'left_hand'] },
    findings: { type: 'array', items: { type: 'object', properties: {
      finding: { type: 'string' }, numbers: { type: 'string' }, evidence_clips: CLIPS, confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      second_check: CHECK, what_changed: { type: 'string' },
    }, required: ['finding', 'numbers', 'evidence_clips', 'confidence', 'second_check', 'what_changed'] } },
    rule_check: { type: 'string' },
    priorities: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, why: { type: 'string' }, cue: { type: 'string' }, evidence_clips: CLIPS, second_check: CHECK, what_changed: { type: 'string' },
    }, required: ['what', 'why', 'cue', 'evidence_clips', 'second_check', 'what_changed'] } },
    drive_notes: { type: 'array', items: { type: 'object', properties: { clip: INT, note: { type: 'string' } }, required: ['clip', 'note'] } },
  },
  required: ['summary', 'counts', 'findings', 'rule_check', 'priorities', 'drive_notes'],
}
const checked = verdicts.map((v, i) => v ? { index: i, verdict: v.verdict, corrected_claim: v.corrected_claim || '', evidence: v.evidence } : null).filter(Boolean)
const finalP = await agent(`You are the head coach. You wrote the drive summary below (SUMMARY) for the player from 13 per-drive records. A skeptical second coach then re-watched the frames behind your first five findings and your first two priorities and returned a verdict and a corrected claim for each (VERDICTS: index 0-4 = findings 1-5 in order, index 5-6 = priorities 1-2). Produce the FINAL version that the player will read, in the structured format.

Rules:
- Where the second coach corrected a number, a count, a clip list or an interpretation, the corrected version wins. Use his corrected claim as the basis of that finding or priority, in plain Hebrew, and put the counts in "numbers". Set second_check = "corrected" and say in what_changed, in one short sentence, what changed against the first version. If he confirmed it unchanged: second_check = "confirmed", what_changed = "".
- Findings and priorities he did not check keep their content with second_check = "not_checked", but any number in them that contradicts a corrected finding must be brought in line with the corrected one (say so in what_changed).
- counts: the corrected counts. beat_defender = clear passes of the first defender only; beat_defender_half_step = drives where he gained only about half a step; tight / wide / lateral / into_chest as the second coach regrouped them (lateral = dribbling without turning toward the basket, into_chest = going straight at a defender).
- summary: 3-5 sentences, rewritten so every number matches the corrected findings. Include the second coach's caveat wherever it changes the meaning of a finding (for example, that going to the side the defender gave may be a habit of leaving to one side and not a read).
- rule_check: keep the explanation of the raised-hand rule with the mirror, then bring the part about where it applied in line with the corrected findings and add the caveat.
- priorities: for a corrected priority, "what" is a short title (at most 12 words), "why" the corrected reasoning, "cue" at most 12 Hebrew words.
- drive_notes: one entry per drive about which the second coach's evidence corrects or adds something specific (side attacked, both sides attacked in one possession, a clear pass versus half a step, a hidden moment, no contact, and so on): one or two short Hebrew sentences. Only drives he actually said something specific about.
- Do not invent anything that is in neither input. Keep every clip number.
${HEBREW}
SUMMARY:
${JSON.stringify(patterns)}

VERDICTS:
${JSON.stringify(checked)}`, { label: 'drive-final', phase: 'Finalize', schema: FINAL })
return { drives: ok.length, findings: (patterns?.findings || []).length, tally, final: !!finalP }

import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont();

/* ------------------------------------------------------------------ */
/* Palette: the project's own colours (navy / blue / yellow), no brand. */
/* ------------------------------------------------------------------ */
export const C = {
  navy: "#0B1F3A",
  navyDeep: "#06142A",
  blue: "#007AC1",
  yellow: "#FDBB30",
  white: "#FFFFFF",
  ink: "#0B1F3A",
};

const FPS = 30;
const s = (sec: number) => Math.round(sec * FPS);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/* ------------------------------------------------------------------ */
/* Timeline                                                            */
/* ------------------------------------------------------------------ */
type Scene =
  | { kind: "solid"; dur: number; lines: string[]; sub?: string; big?: boolean }
  | { kind: "text"; dur: number; words: string; hi: string[] }
  | { kind: "wide"; dur: number; src: string; from?: number; caption?: string; tag?: string }
  | { kind: "square"; dur: number; src: string; from?: number; caption?: string; tag?: string }
  | { kind: "full"; dur: number; src: string; from?: number; caption?: string }
  | { kind: "image"; dur: number; src: string; caption?: string; pan?: boolean; zoom?: boolean }
  | { kind: "end"; dur: number };

const SCENES: Scene[] = [
  { kind: "solid", dur: 3.6, lines: ["Every pickup game", "deserves a recap."], big: true },
  { kind: "text", dur: 2.6, words: "Put a phone on a tripod.", hi: ["phone", "tripod."] },
  { kind: "wide", dur: 3.6, src: "footage/raw.mp4", caption: "One fixed camera. Nothing else.", tag: "RAW VIDEO" },
  { kind: "text", dur: 2.8, words: "Claude Code finds every basket, frame by frame.", hi: ["every", "basket,"] },
  { kind: "square", dur: 4.6, src: "footage/rim_slow.mp4", caption: "Every frame at the rim, 30 a second. A make is the ball going through the net, not near it.", tag: "RIM CHECK" },
  { kind: "text", dur: 2.6, words: "It checks the net moved, not just the ball.", hi: ["net", "moved,"] },
  { kind: "image", dur: 3.6, src: "footage/strip_c000.jpg", caption: "Motion in the net zone, the strands going dark, the ball out of the bottom.", pan: true },
  { kind: "text", dur: 2.6, words: "Names the scorer and the assist.", hi: ["scorer", "assist."] },
  { kind: "wide", dur: 5.2, src: "footage/recap.mp4", caption: "Two independent reviewers per basket. Disagree? A third decides.", tag: "EVERY-BASKET RECAP" },
  { kind: "text", dur: 2.6, words: "A Top 10 that follows the ball.", hi: ["Top", "10"] },
  { kind: "full", dur: 7.5, src: "footage/top10v.mp4", caption: "The vertical window pans with the play. Passer, catch, release, rim." },
  { kind: "text", dur: 2.4, words: "A box score for everyone.", hi: ["box", "score"] },
  { kind: "image", dur: 4.4, src: "footage/box_score_0510.png", zoom: true },
  { kind: "text", dur: 2.6, words: "Your own reel, with live stats.", hi: ["live", "stats."] },
  { kind: "wide", dur: 6.0, src: "footage/reel.mp4", from: 3, caption: "Every possession you touched, to the end of the play. Points and assists pop up as they happen.", tag: "PERSONAL REEL" },
  { kind: "solid", dur: 5.2, lines: ["What you need:", "a paid Claude subscription", "and any laptop."], sub: "No graphics card. The long steps run overnight." },
  { kind: "end", dur: 5.0 },
];

const STARTS: number[] = [];
let acc = 0;
for (const sc of SCENES) {
  STARTS.push(acc);
  acc += s(sc.dur);
}
export const TOTAL_FRAMES = acc;

/* ------------------------------------------------------------------ */
/* Pieces                                                              */
/* ------------------------------------------------------------------ */
const useFadeIn = (frames = 8) => {
  const f = useCurrentFrame();
  return interpolate(f, [0, frames], [0, 1], CLAMP);
};

const Words: React.FC<{ text: string; hi?: string[]; size: number; color?: string; stagger?: number; start?: number; weight?: number; align?: "center" | "left" }> = ({
  text, hi = [], size, color = C.white, stagger = 3, start = 4, weight = 700, align = "center",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: align === "center" ? "center" : "flex-start", gap: `0 ${size * 0.26}px`, lineHeight: 1.18 }}>
      {words.map((w, i) => {
        const delay = start + i * stagger;
        const p = spring({ frame, fps, delay, config: { damping: 14, stiffness: 180, mass: 0.6 } });
        const op = interpolate(frame, [delay, delay + 6], [0, 1], CLAMP);
        const isHi = hi.includes(w);
        return (
          <span key={i} style={{
            display: "inline-block",
            fontFamily, fontWeight: weight, fontSize: size, color: isHi ? C.yellow : color,
            opacity: op, transform: `translateY(${(1 - p) * size * 0.35}px) scale(${0.92 + p * 0.08})`,
            letterSpacing: -size * 0.02,
          }}>{w}</span>
        );
      })}
    </div>
  );
};

const Solid: React.FC<{ lines: string[]; sub?: string; big?: boolean }> = ({ lines, sub, big }) => {
  const frame = useCurrentFrame();
  const subOp = interpolate(frame, [40, 55], [0, 1], CLAMP);
  return (
    <AbsoluteFill style={{ backgroundColor: C.blue, justifyContent: "center", alignItems: "center", padding: "0 90px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 14, alignItems: "center" }}>
        {lines.map((l, i) => (
          <Words key={i} text={l} size={big ? 92 : 76} start={6 + i * 10} stagger={3} />
        ))}
      </div>
      {sub ? (
        <div style={{ position: "absolute", bottom: 300, left: 90, right: 90, textAlign: "center", fontFamily, fontWeight: 600, fontSize: 40, color: "rgba(255,255,255,0.88)", opacity: subOp, lineHeight: 1.35 }}>{sub}</div>
      ) : null}
    </AbsoluteFill>
  );
};

const TextCard: React.FC<{ words: string; hi: string[] }> = ({ words, hi }) => (
  <AbsoluteFill style={{ backgroundColor: C.navy, justifyContent: "center", alignItems: "center", padding: "0 100px" }}>
    <Words text={words} hi={hi} size={80} start={3} stagger={2} />
  </AbsoluteFill>
);

const Tag: React.FC<{ text: string; top: number }> = ({ text, top }) => {
  const op = useFadeIn(10);
  return (
    <div style={{ position: "absolute", top, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: op }}>
      <div style={{ fontFamily, fontWeight: 700, fontSize: 26, letterSpacing: 4, color: C.yellow, background: "rgba(0,0,0,0.35)", padding: "10px 22px", borderRadius: 6 }}>{text}</div>
    </div>
  );
};

const Caption: React.FC<{ text: string; bottom?: number; delay?: number }> = ({ text, bottom = 280, delay = 10 }) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [delay, delay + 10], [0, 1], CLAMP);
  const y = interpolate(frame, [delay, delay + 10], [16, 0], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  return (
    <div style={{ position: "absolute", bottom, left: 80, right: 80, textAlign: "center", opacity: op, transform: `translateY(${y}px)` }}>
      <div style={{ fontFamily, fontWeight: 600, fontSize: 40, lineHeight: 1.35, color: C.white, textShadow: "0 2px 16px rgba(0,0,0,0.6)" }}>{text}</div>
    </div>
  );
};

const Frame: React.FC<{ w: number; h: number; children: React.ReactNode; y?: number }> = ({ w, h, children, y = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 18, stiffness: 120, mass: 0.8 } });
  const op = interpolate(frame, [0, 8], [0, 1], CLAMP);
  return (
    <div style={{
      position: "absolute", left: (1080 - w) / 2, top: (1920 - h) / 2 + y, width: w, height: h, overflow: "hidden",
      borderRadius: 16, boxShadow: "0 30px 80px rgba(0,0,0,0.55)", opacity: op,
      transform: `scale(${0.96 + p * 0.04})`, background: "#000",
    }}>{children}</div>
  );
};

const Wide: React.FC<{ src: string; from?: number; caption?: string; tag?: string }> = ({ src, from = 0, caption, tag }) => {
  const w = 1000, h = Math.round(w * 9 / 16);
  return (
    <AbsoluteFill style={{ backgroundColor: C.navyDeep }}>
      {tag ? <Tag text={tag} top={(1920 - h) / 2 - 150} /> : null}
      <Frame w={w} h={h} y={-80}>
        <OffthreadVideo src={staticFile(src)} startFrom={s(from)} muted style={{ width: w, height: h, objectFit: "cover" }} />
      </Frame>
      {caption ? <Caption text={caption} bottom={(1920 - h) / 2 - 80 - 180} /> : null}
    </AbsoluteFill>
  );
};

const Square: React.FC<{ src: string; from?: number; caption?: string; tag?: string }> = ({ src, from = 0, caption, tag }) => {
  const w = 1000, h = 1000;
  return (
    <AbsoluteFill style={{ backgroundColor: C.navyDeep }}>
      {tag ? <Tag text={tag} top={(1920 - h) / 2 - 150 - 60} /> : null}
      <Frame w={w} h={h} y={-60}>
        <OffthreadVideo src={staticFile(src)} startFrom={s(from)} muted style={{ width: w, height: h, objectFit: "cover" }} />
      </Frame>
      {caption ? <Caption text={caption} bottom={(1920 - h) / 2 - 60 - 170} /> : null}
    </AbsoluteFill>
  );
};

const Full: React.FC<{ src: string; from?: number; caption?: string }> = ({ src, from = 0, caption }) => {
  const op = useFadeIn(8);
  return (
    <AbsoluteFill style={{ backgroundColor: C.navyDeep, opacity: op }}>
      <OffthreadVideo src={staticFile(src)} startFrom={s(from)} muted style={{ width: 1080, height: 1920, objectFit: "cover" }} />
      {caption ? (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, padding: "120px 80px 170px", background: "linear-gradient(180deg, rgba(6,20,42,0) 0%, rgba(6,20,42,0.85) 60%)" }}>
          <Caption text={caption} bottom={0} />
          <div style={{ height: 120 }} />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const Picture: React.FC<{ src: string; caption?: string; pan?: boolean; zoom?: boolean; dur: number }> = ({ src, caption, pan, zoom, dur }) => {
  const frame = useCurrentFrame();
  const op = useFadeIn(8);
  const t = interpolate(frame, [0, s(dur)], [0, 1], CLAMP);
  if (zoom) {
    const sc = 1 + t * 0.06;
    return (
      <AbsoluteFill style={{ backgroundColor: C.navyDeep, opacity: op }}>
        <Img src={staticFile(src)} style={{ width: 1080, height: 1920, objectFit: "cover", transform: `scale(${sc})`, transformOrigin: "50% 30%" }} />
        {caption ? <Caption text={caption} /> : null}
      </AbsoluteFill>
    );
  }
  // pan: a wide strip shown inside a frame, sliding slowly to the left
  const w = 1000, h = 1000;
  const x = -t * 1400;
  return (
    <AbsoluteFill style={{ backgroundColor: C.navyDeep }}>
      <Tag text="NET STRANDS" top={(1920 - h) / 2 - 150 - 60} />
      <Frame w={w} h={h} y={-60}>
        <Img src={staticFile(src)} style={{ height: h, width: "auto", transform: `translateX(${x}px)`, display: "block" }} />
      </Frame>
      {caption ? <Caption text={caption} bottom={(1920 - h) / 2 - 60 - 170} /> : null}
    </AbsoluteFill>
  );
};

const End: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, delay: 4, config: { damping: 14, stiffness: 150 } });
  const op2 = interpolate(frame, [22, 36], [0, 1], CLAMP);
  const op3 = interpolate(frame, [40, 54], [0, 1], CLAMP);
  return (
    <AbsoluteFill style={{ backgroundColor: C.blue, justifyContent: "center", alignItems: "center", padding: "0 80px" }}>
      <div style={{ transform: `scale(${0.9 + p * 0.1})`, opacity: p, textAlign: "center" }}>
        <div style={{ fontFamily, fontWeight: 700, fontSize: 116, color: C.white, letterSpacing: -3, lineHeight: 1 }}>courtside-ai</div>
        <div style={{ fontFamily, fontWeight: 600, fontSize: 40, color: "rgba(255,255,255,0.9)", marginTop: 26 }}>Pickup game in. Recap, Top 10, box score out.</div>
      </div>
      <div style={{ position: "absolute", bottom: 330, left: 0, right: 0, textAlign: "center", opacity: op2 }}>
        <div style={{ fontFamily, fontWeight: 700, fontSize: 44, color: C.ink, background: C.yellow, display: "inline-block", padding: "18px 34px", borderRadius: 6 }}>github.com/bshireto/courtside-ai</div>
        <div style={{ fontFamily, fontWeight: 600, fontSize: 32, color: "rgba(255,255,255,0.9)", marginTop: 26 }}>Open source. Built with Claude Code.</div>
      </div>
      <div style={{ position: "absolute", bottom: 90, left: 60, right: 60, textAlign: "center", opacity: op3, fontFamily, fontWeight: 500, fontSize: 22, color: "rgba(255,255,255,0.75)", lineHeight: 1.5 }}>
        Music: "Funky Chunk" by Kevin MacLeod (incompetech.com)<br />Licensed under Creative Commons: By Attribution 4.0
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Composition                                                         */
/* ------------------------------------------------------------------ */
export const Explainer: React.FC = () => {
  const frame = useCurrentFrame();
  const musicVol = interpolate(frame, [0, 20, TOTAL_FRAMES - 60, TOTAL_FRAMES], [0, 0.55, 0.55, 0], CLAMP);
  return (
    <AbsoluteFill style={{ backgroundColor: C.navy }}>
      <Audio src={staticFile("audio/music.mp3")} volume={musicVol} />
      {SCENES.map((sc, i) => (
        <Sequence key={i} from={STARTS[i]} durationInFrames={s(sc.dur)} name={`${i}-${sc.kind}`}>
          {sc.kind === "solid" ? <Solid lines={sc.lines} sub={sc.sub} big={sc.big} /> : null}
          {sc.kind === "text" ? <TextCard words={sc.words} hi={sc.hi} /> : null}
          {sc.kind === "wide" ? <Wide src={sc.src} from={sc.from} caption={sc.caption} tag={sc.tag} /> : null}
          {sc.kind === "square" ? <Square src={sc.src} from={sc.from} caption={sc.caption} tag={sc.tag} /> : null}
          {sc.kind === "full" ? <Full src={sc.src} from={sc.from} caption={sc.caption} /> : null}
          {sc.kind === "image" ? <Picture src={sc.src} caption={sc.caption} pan={sc.pan} zoom={sc.zoom} dur={sc.dur} /> : null}
          {sc.kind === "end" ? <End /> : null}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

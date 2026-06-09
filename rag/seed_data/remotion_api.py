"""Remotion API reference snippets — one concept per chunk.

Each entry is a self-contained code example with an explanatory comment.
Never combine multiple API concepts in one chunk.
"""

REMOTION_API_DOCS: list[str] = [
    # ── useCurrentFrame + interpolate ────────────────────────────────────────
    """\
// useCurrentFrame and interpolate: animate a value over time
import { useCurrentFrame, interpolate } from "remotion";

export const FadeInText: React.FC = () => {
  const frame = useCurrentFrame();
  // Fade from 0 to 1 between frames 0 and 20
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <div style={{ opacity }}>Hello, World!</div>;
};
// useCurrentFrame() returns the current frame number (starts at 0).
// interpolate() maps an input range to an output range linearly.
""",

    # ── Sequence ─────────────────────────────────────────────────────────────
    """\
// Sequence: render a child component starting at a specific frame
import { Sequence } from "remotion";

export const MyComposition: React.FC = () => (
  <AbsoluteFill>
    {/* Scene 1 starts at frame 0 and lasts 90 frames (3 s at 30 fps) */}
    <Sequence from={0} durationInFrames={90}>
      <Scene1 />
    </Sequence>
    {/* Scene 2 starts at frame 90 and lasts 60 frames (2 s) */}
    <Sequence from={90} durationInFrames={60}>
      <Scene2 />
    </Sequence>
  </AbsoluteFill>
);
// 'from' is the absolute start frame; 'durationInFrames' limits rendering.
// useCurrentFrame() inside a Sequence resets to 0 at its start frame.
""",

    # ── AbsoluteFill ─────────────────────────────────────────────────────────
    """\
// AbsoluteFill: a div that fills 100 % of the composition canvas
import { AbsoluteFill } from "remotion";

export const Background: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#1a1a2e" }}>
    {/* Everything inside is positioned relative to the full canvas */}
    <h1 style={{ color: "white", textAlign: "center" }}>FotoOwl</h1>
  </AbsoluteFill>
);
// Equivalent to: position: absolute; top:0; left:0; right:0; bottom:0
// Always use AbsoluteFill as the root wrapper for each scene.
""",

    # ── Img component ────────────────────────────────────────────────────────
    """\
// Img: display an image with Remotion's asset-aware Img component
import { Img, staticFile } from "remotion";

export const PhotoScene: React.FC<{ filename: string }> = ({ filename }) => (
  <AbsoluteFill>
    <Img
      src={staticFile(\`images/\${filename}\`)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </AbsoluteFill>
);
// Always use <Img> instead of <img> so Remotion can preload assets.
// staticFile() resolves paths from the public/ directory at render time.
""",

    # ── spring() ─────────────────────────────────────────────────────────────
    """\
// spring(): physics-based animation that feels natural
import { useCurrentFrame, useVideoConfig, spring } from "remotion";

export const SpringScale: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 100, mass: 1 },
    from: 0.8,
    to: 1.0,
  });
  return (
    <div style={{ transform: \`scale(\${scale})\` }}>
      <img src={staticFile("images/photo.jpg")} />
    </div>
  );
};
// spring() converges naturally without needing manual clamping.
// Adjust damping (smoothness) and stiffness (speed) for different feels.
""",

    # ── Series ───────────────────────────────────────────────────────────────
    """\
// Series: compose sequential scenes without manual frame math
import { Series } from "remotion";

export const SlideShow: React.FC = () => (
  <AbsoluteFill>
    <Series>
      {/* Each child auto-starts after the previous one ends */}
      <Series.Sequence durationInFrames={90}>
        <Scene1 />
      </Series.Sequence>
      <Series.Sequence durationInFrames={60}>
        <Scene2 />
      </Series.Sequence>
      <Series.Sequence durationInFrames={120}>
        <Scene3 />
      </Series.Sequence>
    </Series>
  </AbsoluteFill>
);
// Series is the recommended way to build slide-show style compositions.
// Total duration = sum of all durationInFrames values.
""",

    # ── Audio ────────────────────────────────────────────────────────────────
    """\
// Audio: add background music or sound effects
import { Audio, staticFile } from "remotion";

export const WithMusic: React.FC = () => (
  <AbsoluteFill>
    <Audio
      src={staticFile("audio/background.mp3")}
      volume={0.6}
      startFrom={0}
    />
    {/* Visual content renders on top of the Audio component */}
    <MyVisuals />
  </AbsoluteFill>
);
// Audio must be placed inside AbsoluteFill alongside visual components.
// 'volume' accepts 0–1. 'startFrom' offsets the audio start in frames.
""",

    # ── staticFile() ─────────────────────────────────────────────────────────
    """\
// staticFile(): resolve a path to an asset in the public/ directory
import { staticFile, Img } from "remotion";

// Correct usage — always use staticFile() for local assets
const photoSrc = staticFile("images/wedding_001.jpg");
const audioSrc = staticFile("audio/music.mp3");

export const AssetDemo: React.FC = () => (
  <AbsoluteFill>
    <Img src={photoSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    <Audio src={audioSrc} volume={0.5} />
  </AbsoluteFill>
);
// Never use relative paths like "./images/..." — they break during rendering.
// staticFile() works in both preview (dev server) and final render.
""",
]

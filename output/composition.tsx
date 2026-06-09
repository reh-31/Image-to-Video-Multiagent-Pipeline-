import React from 'react';
import { AbsoluteFill, Img, Audio, Series, interpolate, useCurrentFrame, staticFile, registerRoot, Composition } from 'remotion';

const SceneTemplate: React.FC<{ image: string; caption: string; durationInFrames: number; audio: string }> = ({ image, caption, durationInFrames, audio }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const scale = interpolate(frame, [0, durationInFrames], [1, 1.04], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill>
      <Img src={staticFile(image)} style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(24px) brightness(0.45) saturate(1.2)', transform: 'scale(1.08)', position: 'absolute' }} />
      <AbsoluteFill style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Img src={staticFile(image)} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', position: 'relative', zIndex: 1, opacity, transform: `scale(${scale})` }} />
      </AbsoluteFill>
      <div style={{ position: 'absolute', bottom: '8%', width: '100%', textAlign: 'center', opacity, fontFamily: 'serif', fontSize: '48px', color: 'white', zIndex: 2 }}>
        <div style={{ maxWidth: '80%', margin: '0 auto' }}>{caption}</div>
      </div>
      <Audio
        src={staticFile(audio)}
        startFrom={0}
        volume={(f) => interpolate(f, [0, 8, durationInFrames - 15, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}
      />
    </AbsoluteFill>
  );
};

const MyComposition: React.FC = () => (
  <Series>
    <Series.Sequence durationInFrames={150}>
      <SceneTemplate image="_ASL9923.jpg" caption="where the journey begins" durationInFrames={150} audio="audio/scene_0.mp3" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={150}>
      <SceneTemplate image="_ASL9984.jpg" caption="two hearts beat as one" durationInFrames={150} audio="audio/scene_1.mp3" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={150}>
      <SceneTemplate image="_ASL9971.jpg" caption="a promise held in silence" durationInFrames={150} audio="audio/scene_2.mp3" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={150}>
      <SceneTemplate image="_ASL9969.jpg" caption="tethered by grace" durationInFrames={150} audio="audio/scene_3.mp3" />
    </Series.Sequence>
    <Series.Sequence durationInFrames={150}>
      <SceneTemplate image="_ASL9976.jpg" caption="forever finds us here" durationInFrames={150} audio="audio/scene_4.mp3" />
    </Series.Sequence>
  </Series>
);

const MyRoot: React.FC = () => (
  <Composition id="MyComposition" component={MyComposition} durationInFrames={750} fps={30} width={1920} height={1080} />
);

registerRoot(MyRoot);
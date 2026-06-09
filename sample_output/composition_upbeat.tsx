import React from 'react';
import {
  AbsoluteFill,
  Img,
  Series,
  Audio,
  useCurrentFrame,
  interpolate,
  staticFile,
  registerRoot,
  Composition,
} from 'remotion';

interface SceneProps {
  image: string;
  caption: string;
  audio: string;
  duration: number;
}

const Scene: React.FC<SceneProps> = ({ image, caption, audio, duration }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const scale = interpolate(frame, [0, duration], [1, 1.04], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Img
        src={staticFile(image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'blur(24px) brightness(0.45) saturate(1.2)',
          transform: 'scale(1.08)',
          position: 'absolute',
        }}
      />
      <AbsoluteFill
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Img
          src={staticFile(image)}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            position: 'relative',
            zIndex: 1,
            opacity,
            transform: `scale(${scale})`,
          }}
        />
      </AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          bottom: '8%',
          width: '80%',
          left: '10%',
          textAlign: 'center',
          color: 'white',
          fontFamily: 'serif',
          fontSize: '48px',
          opacity,
        }}
      >
        {caption}
      </div>
      <Audio
        src={staticFile(audio)}
        startFrom={0}
        volume={(f) =>
          interpolate(
            f,
            [0, 8, duration - 15, duration],
            [0, 1, 1, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          )
        }
      />
    </AbsoluteFill>
  );
};

export const MyComposition: React.FC = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={150}>
          <Scene
            image="_ASL9923.jpg"
            caption="where our story begins"
            audio="audio/scene_0.mp3"
            duration={150}
          />
        </Series.Sequence>
        <Series.Sequence durationInFrames={150}>
          <Scene
            image="_ASL9969.jpg"
            caption="two souls, one heartbeat"
            audio="audio/scene_1.mp3"
            duration={150}
          />
        </Series.Sequence>
        <Series.Sequence durationInFrames={150}>
          <Scene
            image="_ASL9984.jpg"
            caption="a promise held in a smile"
            audio="audio/scene_2.mp3"
            duration={150}
          />
        </Series.Sequence>
        <Series.Sequence durationInFrames={150}>
          <Scene
            image="_ASL9971.jpg"
            caption="cherishing this quiet grace"
            audio="audio/scene_3.mp3"
            duration={150}
          />
        </Series.Sequence>
        <Series.Sequence durationInFrames={150}>
          <Scene
            image="_ASL9976.jpg"
            caption="forever starts today"
            audio="audio/scene_4.mp3"
            duration={150}
          />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};

const MyRoot: React.FC = () => {
  return (
    <Composition
      id="MyComposition"
      component={MyComposition}
      durationInFrames={750}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};

registerRoot(MyRoot);
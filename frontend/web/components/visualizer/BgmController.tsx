'use client';

import type React from 'react';
import { useEffect, useRef, useState } from 'react';
import { useAudioContextState } from './audio-context-provider';
import { Button } from '../ui/button';
import { PlayIcon, StopIcon } from '../icons';

type Props = {
  src: string; // BGM音源のURL
};

const BgmController: React.FC<Props> = ({ src }) => {
  const { audioCtx } = useAudioContextState();

  // AudioBufferを保持
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  // 再生中のAudioBufferSourceNodeを参照
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);

  // BGMをfetchしてdecodeAudioDataする
  useEffect(() => {
    if (!audioCtx) return; // initAudio()がまだ呼ばれてない場合は待つ
    let cancelled = false;

    const loadBgm = async () => {
      try {
        const resp = await fetch(src);
        const arrayBuf = await resp.arrayBuffer();
        const decoded = await audioCtx.decodeAudioData(arrayBuf);
        if (!cancelled) {
          setAudioBuffer(decoded);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadBgm();

    return () => {
      cancelled = true;
    };
  }, [src, audioCtx]);

  // 再生開始
  const handlePlay = () => {
    if (!audioCtx || !audioBuffer) return;
    // 既に再生中なら止める
    if (sourceRef.current) {
      sourceRef.current.stop();
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    // 新しく AudioBufferSourceNode を作り、destinationに接続
    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.loop = false; // ループさせる場合
    source.connect(audioCtx.destination);

    source.start(0);
    sourceRef.current = source;
  };

  // 停止
  const handleStop = () => {
    if (sourceRef.current) {
      sourceRef.current.stop();
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
  };

  const running = !!sourceRef.current;

  return (
    <div>
      {!running && (
        <Button onClick={handlePlay} disabled={!audioBuffer}>
          <PlayIcon />
        </Button>
      )}
      {running && (
        <Button onClick={handleStop} disabled={!sourceRef.current}>
          <StopIcon />
        </Button>
      )}
    </div>
  );
};

export default BgmController;

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
  // 再生中の状態を管理するstate
  const [isPlaying, setIsPlaying] = useState(false);
  // 再生中のAudioBufferSourceNodeを参照
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);

  // BGMをfetchしてdecodeAudioDataする
  useEffect(() => {
    if (!audioCtx) return; // initAudio()がまだ呼ばれていない場合は待つ
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

  // 再生/停止の切替処理
  const handleToggle = () => {
    if (!audioCtx || !audioBuffer) return;

    // 再生中なら停止する
    if (isPlaying) {
      if (sourceRef.current) {
        sourceRef.current.stop();
        sourceRef.current.disconnect();
        sourceRef.current = null;
      }
      setIsPlaying(false);
    } else {
      // 新しい AudioBufferSourceNode を作成し、接続
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.loop = false; // ループする場合はtrueに変更

      // 再生終了時の処理
      source.onended = () => {
        source.disconnect();
        sourceRef.current = null;
        setIsPlaying(false);
      };

      source.connect(audioCtx.destination);
      source.start(0);
      sourceRef.current = source;
      setIsPlaying(true);
    }
  };

  return (
    <div>
      <Button onClick={handleToggle} disabled={!audioBuffer}>
        {isPlaying ? <StopIcon /> : <PlayIcon />}
      </Button>
    </div>
  );
};

export default BgmController;

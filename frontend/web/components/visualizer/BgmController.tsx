'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useAudioContextState } from './audio-context-provider';
import { Button } from '../ui/button';
import { PlayIcon, StopIcon } from '../icons';
import { MusicIcon } from 'lucide-react';

type Props = {
  src: string; // BGM 音源の URL
};

const BgmController: React.FC<Props> = ({ src }) => {
  const { audioCtx, analyser, initAudio } = useAudioContextState();

  // AudioContext が未初期化ならここで初期化（マイクは使わない）
  useEffect(() => {
    if (!audioCtx) {
      initAudio(undefined, { useMic: false }).catch(console.error);
    }
  }, [audioCtx, initAudio]);

  // AudioBuffer を保持
  const [audioBuffer, setAudioBuffer] = useState<AudioBuffer | null>(null);
  // 再生中の状態を管理
  const [isPlaying, setIsPlaying] = useState(false);
  // 再生中の AudioBufferSourceNode を参照
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);

  // BGM の取得と decode
  useEffect(() => {
    if (!audioCtx) return; // AudioContext 初期化待ち
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

  // 再生／停止の切替処理
  const handleToggle = () => {
    if (!audioCtx || !audioBuffer) return;

    if (isPlaying) {
      // 再生中なら停止
      if (sourceRef.current) {
        sourceRef.current.stop();
        sourceRef.current.disconnect();
        sourceRef.current = null;
      }
      setIsPlaying(false);
    } else {
      // 新しい AudioBufferSourceNode を作成して接続
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.loop = false; // ループ再生する場合は true に変更

      // 再生終了時の処理
      source.onended = () => {
        source.disconnect();
        sourceRef.current = null;
        setIsPlaying(false);
      };

      // AudioContextProvider 側で作成した analyser に接続（あれば）
      if (analyser) {
        source.connect(analyser);
      } else {
        source.connect(audioCtx.destination);
      }

      source.start(0);
      sourceRef.current = source;
      setIsPlaying(true);
    }
  };

  return (
    <div>
      <Button onClick={handleToggle} disabled={!audioBuffer}>
        {isPlaying ? <StopIcon /> : <MusicIcon />}
      </Button>
    </div>
  );
};

export default BgmController;

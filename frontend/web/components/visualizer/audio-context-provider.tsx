// components/visualizer/audio-context-provider.tsx
'use client';

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

interface AudioContextValue {
  audioCtx: AudioContext | null;
  analyser: AnalyserNode | null;
  freqData: Uint8Array | null;
  micAllowed: boolean;
  /**
   * @param mediaElement 渡された場合、その音源を analyser に接続します（既に接続済みなら何もしません）
   * @param options.useMic true を指定すると、mediaElement がない場合にマイク入力を利用
   */
  initAudio: (
    mediaElement?: HTMLMediaElement,
    options?: { useMic?: boolean },
  ) => Promise<void>;
}

const AudioContextState = createContext<AudioContextValue>({
  audioCtx: null,
  analyser: null,
  freqData: null,
  micAllowed: false,
  initAudio: async () => {},
});

// 接続済みの mediaElement を管理（同じ要素を複数回接続しないように）
const connectedMediaElements = new WeakSet<HTMLMediaElement>();

export const AudioProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [audioCtx, setAudioCtx] = useState<AudioContext | null>(null);
  const [freqData, setFreqData] = useState<Uint8Array | null>(null);
  const [micAllowed, setMicAllowed] = useState(false);

  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const rafIdRef = useRef<number | null>(null);

  const initAudio = async (
    mediaElement?: HTMLMediaElement,
    options?: { useMic?: boolean },
  ) => {
    // AudioContext が未生成なら生成
    if (!audioCtx) {
      const AC = window.AudioContext || (window as any).webkitAudioContext;
      if (!AC) throw new Error('AudioContext not supported');

      const ctx = new AC();
      setAudioCtx(ctx);

      // AnalyserNode の作成
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.85;
      analyserRef.current = analyser;

      // 接続先は一旦 analyser → destination（すべての音源が混ざって出力される）
      analyser.connect(ctx.destination);

      // 周波数データ用バッファ
      const bufferLength = analyser.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);

      // 周期的に周波数データを取得
      const tick = () => {
        if (!analyserRef.current || !dataArrayRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArrayRef.current);
        setFreqData(new Uint8Array(dataArrayRef.current));
        rafIdRef.current = requestAnimationFrame(tick);
      };
      tick();
    }

    // AudioContext が既にある場合、渡された mediaElement を接続
    if (audioCtx && mediaElement && !connectedMediaElements.has(mediaElement)) {
      try {
        const source = audioCtx.createMediaElementSource(mediaElement);
        source.connect(analyserRef.current!);
        connectedMediaElements.add(mediaElement);
      } catch (err) {
        console.error('Error connecting media element:', err);
      }
    }

    // オプションでマイク入力を利用（mediaElement が無い場合のみ）
    if (!mediaElement && options?.useMic && audioCtx) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        setMicAllowed(true);
        const micSource = audioCtx.createMediaStreamSource(stream);
        micSource.connect(analyserRef.current!);
      } catch (err) {
        console.error(err);
        setMicAllowed(false);
      }
    }
  };

  // クリーンアップ処理
  useEffect(() => {
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      if (audioCtx) audioCtx.close();
    };
  }, [audioCtx]);

  return (
    <AudioContextState.Provider
      value={{
        audioCtx,
        analyser: analyserRef.current,
        freqData,
        micAllowed,
        initAudio,
      }}
    >
      {children}
    </AudioContextState.Provider>
  );
};

export const useAudioContextState = () => useContext(AudioContextState);

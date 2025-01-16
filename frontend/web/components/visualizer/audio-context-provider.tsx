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
  freqData: Uint8Array | null; // マイクの周波数スペクトル
  micAllowed: boolean;
  initAudio: () => Promise<void>;
}

const AudioContextState = createContext<AudioContextValue>({
  audioCtx: null,
  freqData: null,
  micAllowed: false,
  initAudio: async () => {},
});

export const AudioProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [audioCtx, setAudioCtx] = useState<AudioContext | null>(null);
  const [freqData, setFreqData] = useState<Uint8Array | null>(null);
  const [micAllowed, setMicAllowed] = useState(false);

  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const rafIdRef = useRef<number | null>(null);

  /**
   * ユーザ操作で呼んでもらう想定
   *  - AudioContext作成
   *  - マイクをgetUserMedia
   *  - AnalyserNodeに接続
   *  - requestAnimationFrameで周波数データを取得
   */
  const initAudio = async () => {
    if (audioCtx) return; // 既に初期化済みなら何もしない

    try {
      const AC = window.AudioContext || (window as any).webkitAudioContext;
      if (!AC) throw new Error('AudioContext not supported');

      const ctx = new AC();
      setAudioCtx(ctx);

      // アナライザ
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512; // 2の乗数
      analyser.smoothingTimeConstant = 0.85;
      analyserRef.current = analyser;

      // マイク
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicAllowed(true);
      const micSource = ctx.createMediaStreamSource(stream);
      micSource.connect(analyser);

      // もしマイク音をスピーカーに出したくないなら analyser→ctx.destination は繋がない
      // analyser.connect(ctx.destination);

      // 周波数取得用バッファ
      const bufferLength = analyser.frequencyBinCount; // 256
      dataArrayRef.current = new Uint8Array(bufferLength);

      // 周期的にgetByteFrequencyData()で取得
      const tick = () => {
        if (!analyserRef.current || !dataArrayRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArrayRef.current);

        // 周波数データをStateに反映
        setFreqData(new Uint8Array(dataArrayRef.current));
        rafIdRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch (err) {
      console.error(err);
      setMicAllowed(false);
    }
  };

  // cleanup
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

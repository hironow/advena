import { useEffect, useRef } from 'react';

export function useRafLoop(callback: (deltaMs: number) => void) {
  const requestIdRef = useRef<number | null>(null);
  const previousTimeRef = useRef<number>(performance.now());

  const loop = (currentTime: number) => {
    const delta = currentTime - previousTimeRef.current;
    previousTimeRef.current = currentTime;

    callback(delta);

    requestIdRef.current = requestAnimationFrame(loop);
  };

  useEffect(() => {
    requestIdRef.current = requestAnimationFrame(loop);

    return () => {
      if (requestIdRef.current !== null) {
        cancelAnimationFrame(requestIdRef.current);
      }
    };
  }, []);

  return null;
}

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';

import {
  mockRequestAnimationFrame,
  mockCancelAnimationFrame,
} from '@/tests/hooks/mock-raf';
import { useRafLoop } from '@/hooks/use-ref-loop';

describe('useRafLoop', () => {
  let mockCallback: (deltaMs: number) => void;
  let originalRAF: typeof globalThis.requestAnimationFrame;
  let originalCAF: typeof globalThis.cancelAnimationFrame;

  beforeEach(() => {
    vi.useFakeTimers();
    mockCallback = vi.fn();

    // 元の関数を退避
    originalRAF = globalThis.requestAnimationFrame;
    originalCAF = globalThis.cancelAnimationFrame;

    // モックを差し替え
    globalThis.requestAnimationFrame = vi.fn(mockRequestAnimationFrame);
    globalThis.cancelAnimationFrame = vi.fn(mockCancelAnimationFrame);
  });

  afterEach(() => {
    vi.useRealTimers();

    // 元に戻す
    globalThis.requestAnimationFrame = originalRAF;
    globalThis.cancelAnimationFrame = originalCAF;
  });

  it('renders without error and starts the loop', () => {
    // given
    renderHook(() => useRafLoop(mockCallback));

    // 最初はコールバックは呼ばれていない
    expect(mockCallback).toHaveBeenCalledTimes(0);

    // when
    // 1フレーム分（16ms）進める NOTE: 無限ループになるので 1 フレームだけ進める
    vi.advanceTimersByTime(16);

    // then
    // コールバックが1回呼ばれる
    expect(mockCallback).toHaveBeenCalledTimes(1);

    const [deltaMs] = mockCallback.mock.calls[0];
    expect(typeof deltaMs).toBe('number');
  });

  it('calls callback repeatedly as the frames advance', () => {
    // given
    renderHook(() => useRafLoop(mockCallback));

    expect(mockCallback).toHaveBeenCalledTimes(0);

    // when
    // 3フレーム分進める NOTE: 無限ループになるので 3 フレームだけ進める
    vi.advanceTimersByTime(16 * 3);

    // then
    expect(mockCallback).toHaveBeenCalledTimes(3);
  });

  it('cancels animation on unmount', () => {
    // given
    const { unmount } = renderHook(() => useRafLoop(mockCallback));

    // 2フレーム進める NOTE: 無限ループになるので 2 フレームだけ進める
    vi.advanceTimersByTime(16 * 2);
    expect(mockCallback).toHaveBeenCalledTimes(2);

    // when
    // アンマウント
    unmount();

    // then
    // アンマウント後さらに2フレーム進めても呼ばれないはず
    vi.advanceTimersByTime(16 * 2);
    expect(mockCallback).toHaveBeenCalledTimes(2);

    // cancelAnimationFrame がコールされたか
    expect(globalThis.cancelAnimationFrame).toHaveBeenCalled();
  });
});

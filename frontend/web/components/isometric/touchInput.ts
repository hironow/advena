// touchInput.ts

import { consoleLogWithStyle } from './utils';

// タッチ時の状態を保持
// 複数指タッチをどう扱うか？ → シンプルに「最初の1本」だけ見る想定で実装
export const touchState = {
  active: false,
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0,
  identifier: null as null | number,
};

/**
 * タッチイベントリスナを登録
 */
export function initTouchListeners(element: HTMLElement) {
  const onTouchStart = (e: TouchEvent) => {
    if (touchState.active) return; // すでに他のタッチを処理中なら無視
    if (e.touches.length > 0) {
      const t = e.touches[0];
      touchState.active = true;
      touchState.identifier = t.identifier;
      touchState.startX = t.clientX;
      touchState.startY = t.clientY;
      touchState.currentX = t.clientX;
      touchState.currentY = t.clientY;
    }
    // スクロールを抑止したい場合
    // e.preventDefault();
  };

  const onTouchMove = (e: TouchEvent) => {
    if (!touchState.active) return;
    // 対象のタッチを探す
    for (let i = 0; i < e.touches.length; i++) {
      const t = e.touches[i];
      if (t.identifier === touchState.identifier) {
        touchState.currentX = t.clientX;
        touchState.currentY = t.clientY;
        break;
      }
    }
    // e.preventDefault();
  };

  const endTouch = (id: number) => {
    // タッチが離れたときに identifier が一致するなら状態リセット
    if (touchState.active && touchState.identifier === id) {
      touchState.active = false;
      touchState.identifier = null;
    }
  };

  const onTouchEnd = (e: TouchEvent) => {
    for (let i = 0; i < e.changedTouches.length; i++) {
      endTouch(e.changedTouches[i].identifier);
    }
    // e.preventDefault();
  };

  const onTouchCancel = (e: TouchEvent) => {
    for (let i = 0; i < e.changedTouches.length; i++) {
      endTouch(e.changedTouches[i].identifier);
    }
    // e.preventDefault();
  };

  element.addEventListener('touchstart', onTouchStart, { passive: false });
  element.addEventListener('touchmove', onTouchMove, { passive: false });
  element.addEventListener('touchend', onTouchEnd, { passive: false });
  element.addEventListener('touchcancel', onTouchCancel, { passive: false });

  consoleLogWithStyle('%cisometric%c TouchInput listeners initialized');

  // アンマウント時に解除するなら
  return () => {
    element.removeEventListener('touchstart', onTouchStart);
    element.removeEventListener('touchmove', onTouchMove);
    element.removeEventListener('touchend', onTouchEnd);
    element.removeEventListener('touchcancel', onTouchCancel);
  };
}

/**
 * タッチによる移動ベクトルを取得する（-1〜1の範囲で正規化）
 * 最大移動距離(ピクセル)を joystickRadius として扱い、越えたらクランプ
 */
export function getTouchVector(joystickRadius = 80) {
  if (!touchState.active) {
    return { vx: 0, vy: 0 };
  }
  const dx = touchState.currentX - touchState.startX;
  const dy = touchState.currentY - touchState.startY;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist < 1) {
    return { vx: 0, vy: 0 };
  }
  // clamp
  const clampedDist = Math.min(dist, joystickRadius);
  const ratio = clampedDist / dist; // 0〜1
  // 正規化 ( -1〜1 ぐらいの範囲想定 )
  const vx = (dx * ratio) / joystickRadius;
  const vy = (dy * ratio) / joystickRadius;

  return { vx, vy };
}

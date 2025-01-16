'use client';

import React, { useEffect, useRef } from 'react';
import { keysDown } from './keyInput';
import { initTouchListeners, getTouchVector } from './touchInput';
import { bird1, clock1, getTilePosition, power1, WORLD_SIZE } from './tileset';
import { useRafLoop } from '../../hooks/use-ref-loop';
import Tile from './Tile';

const tileSpeed = 2.0; // 1秒に2マス進む想定

interface IsometricPlayerProps {
  // 毎フレーム計算した「スクリーン座標」を親に通知するコールバック
  onUpdatePos?: (pxX: number, pxY: number) => void;
}

export default function IsometricPlayer({ onUpdatePos }: IsometricPlayerProps) {
  const tileXRef = useRef<number>(WORLD_SIZE - 2);
  const tileYRef = useRef<number>(WORLD_SIZE - 2);
  const layerRef = useRef<number>(0);

  const playerDivRef = useRef<HTMLDivElement | null>(null);

  useRafLoop((deltaMs) => {
    const dt = deltaMs / 1000;

    // --- 1) PCキー入力をベクトル化
    let vxKey = 0;
    let vyKey = 0;
    if (keysDown.w) vyKey -= 1;
    if (keysDown.s) vyKey += 1;
    if (keysDown.a) vxKey -= 1;
    if (keysDown.d) vxKey += 1;

    // 斜め移動の正規化
    const lenKey = Math.sqrt(vxKey * vxKey + vyKey * vyKey);
    if (lenKey > 0) {
      vxKey /= lenKey;
      vyKey /= lenKey;
    }

    // --- 2) タッチ入力をベクトル化
    const { vx: vxTouch, vy: vyTouch } = getTouchVector(80);

    // --- 3) 合成
    let vx = vxKey + vxTouch;
    let vy = vyKey + vyTouch;
    const len = Math.sqrt(vx * vx + vy * vy);
    if (len > 1) {
      vx /= len;
      vy /= len;
    }

    // --- 4) タイル座標を更新 (0〜WORLD_SIZE-1 でクリップ)
    tileXRef.current = Math.max(
      0,
      Math.min(WORLD_SIZE - 1, tileXRef.current + vx * tileSpeed * dt),
    );
    tileYRef.current = Math.max(
      0,
      Math.min(WORLD_SIZE - 1, tileYRef.current + vy * tileSpeed * dt),
    );

    // --- 5) タイル座標 -> ピクセル座標
    const xInt = Math.floor(tileXRef.current);
    const yInt = Math.floor(tileYRef.current);
    const fracX = tileXRef.current - xInt;
    const fracY = tileYRef.current - yInt;

    const basePos = getTilePosition(xInt, yInt, layerRef.current);
    const plus1X = getTilePosition(xInt + 1, yInt, layerRef.current);
    const plus1Y = getTilePosition(xInt, yInt + 1, layerRef.current);

    const dxX = plus1X.pxX - basePos.pxX;
    const dxY = plus1X.pxY - basePos.pxY;
    const dyX = plus1Y.pxX - basePos.pxX;
    const dyY = plus1Y.pxY - basePos.pxY;

    const finalPxX = basePos.pxX + dxX * fracX + dyX * fracY;
    const finalPxY = basePos.pxY + dxY * fracX + dyY * fracY;

    // --- 6) DOM スタイル反映
    if (playerDivRef.current) {
      // playerDivRef.current.style.left = `${finalPxX}px`;
      // playerDivRef.current.style.top = `${finalPxY}px`;
    }

    // 親に「今の描画座標」を通知 (カメラ用)
    onUpdatePos?.(finalPxX, finalPxY);
    // console.info('[isometric] Player is moved to (', finalPxX, ',', finalPxY, ')');
  });

  // 初回マウント時にタッチイベント設定
  useEffect(() => {
    const cleanup = initTouchListeners(document.body);
    if (playerDivRef.current) {
      // playerDivRef.current.style.position = 'absolute';
      // playerDivRef.current.style.width = '40px';
      // playerDivRef.current.style.height = '40px';
      // playerDivRef.current.style.backgroundColor = 'red';
      // playerDivRef.current.style.zIndex = '999';
      // プレイヤーを見た目で中心合わせ
      // playerDivRef.current.style.transform = 'translate(50%, 100%)';
    }
    console.info('[isometric] Player mounted');
    return () => {
      if (cleanup) cleanup();
    };
  }, []);

  return (
    <div ref={playerDivRef}>
      <Tile tile={clock1} x={0} y={0} layer={0} />
    </div>
  );
}
